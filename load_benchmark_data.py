import sys
import time
from urllib.parse import urlparse

import requests
from neo4j import GraphDatabase
from vars import FILE_PATH, AUTH, URI, BATCH_SIZE, DB


def create_schema(driver):
    """Creates index/unique constraint based on DB type so edge MATCH lookups run in O(1) time."""
    t0 = time.perf_counter()
    with driver.session() as session:
        db_type = DB.upper()
        if "MEMGRAPH" in db_type:
            session.run("CREATE INDEX ON :Paper(id);").consume()
        elif "COGNODB" in db_type or "NEO4J" in db_type:
            session.run(
                "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;"
            ).consume()
        else:
            # Generic fallback: try unique constraint first, then index
            try:
                session.run(
                    "CREATE CONSTRAINT paper_id_unique IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;"
                ).consume()
            except Exception:
                session.run("CREATE INDEX ON :Paper(id);").consume()

    duration = time.perf_counter() - t0
    print(f"[1/3] Index/Constraint on :Paper(id) ready in {duration:.3f}s")

def extract_unique_nodes(file_path):
    """Extracts unique node IDs from edge list in memory."""
    print("[2/3] Extracting unique node set...")
    nodes = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                nodes.add(parts[0])
                nodes.add(parts[1])
    return list(nodes)

def load_nodes(driver, nodes):
    """Ingests all unique nodes via UNWIND batches using CREATE for maximum ingest throughput."""
    query = "UNWIND $batch AS id CREATE (:Paper {id: id})"
    total = len(nodes)
    print(f"Loading {total:,} unique Paper nodes...")
    t0 = time.perf_counter()

    with driver.session() as session:
        for i in range(0, total, BATCH_SIZE):
            batch = nodes[i : i + BATCH_SIZE]
            session.run(query, batch=batch).consume()

    t1 = time.perf_counter()
    elapsed = t1 - t0
    throughput = total / elapsed if elapsed > 0 else 0
    print(f"✓ Committed {total:,} nodes in {elapsed:.2f}s ({throughput:,.1f} nodes/sec)\n")
    return total, elapsed, throughput

def load_edges(driver, file_path):
    """Streams and ingests all directed relationships."""
    query = """
    UNWIND $batch AS edge
    MATCH (src:Paper {id: edge.from_id})
    WITH src, edge
    MATCH (dst:Paper {id: edge.to_id})
    CREATE (src)-[:CITES]->(dst)
    """
    print("[3/3] Streaming relationships into :CITES edges...")
    batch = []
    total_edges = 0
    t0 = time.perf_counter()

    with open(file_path, "r", encoding="utf-8") as f, driver.session() as session:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                batch.append({"from_id": parts[0], "to_id": parts[1]})
                total_edges += 1

                if len(batch) >= BATCH_SIZE:
                    session.run(query, batch=batch).consume()
                    batch = []
                    if total_edges % 50000 == 0:
                        print(f"  Committed: {total_edges:,} edges...")

        # Flush remaining buffer
        if batch:
            session.run(query, batch=batch).consume()

    t1 = time.perf_counter()
    elapsed = t1 - t0
    throughput = total_edges / elapsed if elapsed > 0 else 0
    print(f"✓ Committed {total_edges:,} edges in {elapsed:.2f}s ({throughput:,.1f} edges/sec)\n")
    return total_edges, elapsed, throughput

def verify_state(driver):
    with driver.session() as session:
        nodes = session.run("MATCH (p:Paper) RETURN count(p) AS count").single()["count"]
        edges = session.run("MATCH ()-[r:CITES]->() RETURN count(r) AS count").single()["count"]
    return nodes, edges

def main():
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to database successfully.\n" + "=" * 60)

        total_wall_clock_start = time.perf_counter()

        if DB.upper() != "ARCADEDB":
            create_schema(driver)

        nodes_list = extract_unique_nodes(FILE_PATH)

        node_count, node_time, node_rate = load_nodes(
                driver, nodes_list
            )

        edge_count, edge_time, edge_rate = load_edges(
            driver, FILE_PATH
        )

        total_wall_clock_time = (
            time.perf_counter() - total_wall_clock_start
        )

        v_nodes, v_edges = verify_state(driver)

    print("=" * 60)
    print("DATA LOADING METRICS (SECTION 5.2 REPORT)")
    print("=" * 60)
    print(f"Total Wall-Clock Load Time : {total_wall_clock_time:.2f} seconds")
    print(
        f"Node Ingest Throughput     : "
        f"{node_rate:,.2f} nodes/sec "
        f"({node_count:,} nodes in {node_time:.2f}s)"
    )
    print(
        f"Relationship Ingest Rate   : "
        f"{edge_rate:,.2f} rels/sec "
        f"({edge_count:,} edges in {edge_time:.2f}s)"
    )
    print(
        f"Verified Database State    : "
        f"{v_nodes:,} nodes | {v_edges:,} relationships"
    )
    print("=" * 60)

if __name__ == "__main__":
    main()
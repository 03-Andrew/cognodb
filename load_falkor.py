from vars import GRAPH as graph, FILE_PATH, BATCH_SIZE
from load_benchmark_data import extract_unique_nodes
import time


def create_schema():
    """Creates an index on :Paper(id) for O(1) MATCH lookups."""
    query = "CREATE INDEX FOR (p:Paper) ON (p.id)"
    graph.query(query)
    print("[1/3] Index on :Paper(id) ready")


def load_nodes(nodes):
    """Ingests all unique nodes via UNWIND batches using CREATE for maximum ingest throughput."""
    query = """
    UNWIND $batch AS id
    CREATE (:Paper {id: id})
    """
    total = len(nodes)
    print(f"[2/3] Loading {total:,} unique Paper nodes...")
    t0 = time.perf_counter()

    for i in range(0, total, BATCH_SIZE):
        batch = nodes[i:i + BATCH_SIZE]
        graph.query(query, {"batch": batch})

    elapsed = time.perf_counter() - t0
    throughput = total / elapsed if elapsed > 0 else 0
    print(f"✓ Committed {total:,} nodes in {elapsed:.2f}s ({throughput:,.1f} nodes/sec)\n")
    return total, elapsed, throughput


def load_edges(file_path):
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

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                batch.append({"from_id": parts[0], "to_id": parts[1]})
                total_edges += 1

                if len(batch) >= BATCH_SIZE:
                    graph.query(query, {"batch": batch})
                    batch = []
                    if total_edges % 50000 == 0:
                        print(f"  Committed: {total_edges:,} edges...")

        # Flush remaining buffer
        if batch:
            graph.query(query, {"batch": batch})

    elapsed = time.perf_counter() - t0
    throughput = total_edges / elapsed if elapsed > 0 else 0
    print(f"✓ Committed {total_edges:,} edges in {elapsed:.2f}s ({throughput:,.1f} edges/sec)\n")
    return total_edges, elapsed, throughput


def verify_state():
    nodes = graph.query("MATCH (p:Paper) RETURN count(p) AS count").result_set[0][0]
    edges = graph.query("MATCH ()-[r:CITES]->() RETURN count(r) AS count").result_set[0][0]
    return nodes, edges


def main():
    try:
        graph.query("RETURN 1 AS status")
        print("Connected to FalkorDB successfully.\n" + "=" * 60)
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    total_wall_clock_start = time.perf_counter()

    create_schema()

    nodes_list = extract_unique_nodes(FILE_PATH)
    node_count, node_time, node_rate = load_nodes(nodes_list)

    edge_count, edge_time, edge_rate = load_edges(FILE_PATH)

    total_wall_clock_time = time.perf_counter() - total_wall_clock_start

    v_nodes, v_edges = verify_state()

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
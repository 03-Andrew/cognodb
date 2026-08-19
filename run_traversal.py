import math
import random
import statistics
import time
from neo4j import GraphDatabase
from vars import URI, AUTH

ITERATIONS = 150
WARMUP_RUNS = 25
SAMPLE_POOL_SIZE = 500


def percentile(data, p):
    """Calculates the p-th percentile from an array of numbers."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1


def fetch_random_start_nodes(driver):
    """Samples distinct nodes with outgoing edges for realistic traversals."""
    print("Fetching active node sample pool...")
    with driver.session() as session:
        result = session.run(
            f"""
            MATCH (p:Paper)-[:CITES]->()
            RETURN DISTINCT p.id AS id
            LIMIT {SAMPLE_POOL_SIZE}
            """
        )
        nodes = [record["id"] for record in result]
    
    if not nodes:
        raise RuntimeError("No nodes with outgoing edges found. Check database population.")
    print(f"✓ Sample pool ready with {len(nodes)} distinct starting nodes.\n")
    return nodes


def benchmark_query(driver, workload_name, query_template, node_pool, limit_desc=""):
    latencies = []

    # 1. Warm-up Phase (primes engine cache and query plan)
    with driver.session() as session:
        for _ in range(WARMUP_RUNS):
            target_id = random.choice(node_pool)
            session.run(query_template, id=target_id).consume()

    # 2. Measurement Phase (150 iterations)
    with driver.session() as session:
        for _ in range(ITERATIONS):
            target_id = random.choice(node_pool)
            t0 = time.perf_counter()
            session.run(query_template, id=target_id).consume()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)  # Convert to milliseconds

    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    avg = statistics.mean(latencies)

    print(f"| {workload_name:<32} | {p50:>8.2f} ms | {p95:>8.2f} ms | {p99:>8.2f} ms | {avg:>8.2f} ms |")
    return {"name": workload_name, "p50": p50, "p95": p95, "p99": p99}


def main():
    print(f"Connecting to: {URI}")
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        node_pool = fetch_random_start_nodes(driver)

        print("=" * 80)
        print(f"| {'Workload / Query':<32} | {'p50':>11} | {'p95':>11} | {'p99':>11} | {'avg':>11} |")
        print("=" * 80)

        # 1. Point Lookup (Indexed read)
        benchmark_query(
            driver,
            "Point Lookup (:Paper {id})",
            "MATCH (p:Paper {id: $id}) RETURN p.id",
            node_pool
        )

        # 2. 1-Hop Traversal (Direct citations)
        benchmark_query(
            driver,
            "1-Hop Traversal (:CITES)",
            "MATCH (p:Paper {id: $id})-[:CITES]->(c:Paper) RETURN c.id",
            node_pool
        )

        # 3. 2-Hop Traversal (Citations of citations)
        benchmark_query(
            driver,
            "2-Hop Traversal (:CITES*2)",
            "MATCH (p:Paper {id: $id})-[:CITES*2]->(c:Paper) RETURN count(DISTINCT c)",
            node_pool
        )

        # 4. 3-Hop Traversal (Depth 3 with limit to bound result set)
        benchmark_query(
            driver,
            "3-Hop Traversal (Limit 50)",
            "MATCH (p:Paper {id: $id})-[:CITES*3]->(c:Paper) RETURN c.id LIMIT 50",
            node_pool
        )

        print("=" * 80)


if __name__ == "__main__":
    main()
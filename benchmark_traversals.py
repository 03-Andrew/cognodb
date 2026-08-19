import random
from benchmark_utils import (
    get_driver,
    sample_start_nodes,
    measure_query_latency,
    print_table,
)

ITERATIONS = 150
WARMUP_RUNS = 25


def run_traversal_benchmark():
    with get_driver() as driver:
        print("Connected. Sampling candidate start nodes...")
        node_pool = sample_start_nodes(driver, limit=500)
        print(f"Sampled {len(node_pool)} starting nodes with outgoing citations.\n")

        workloads = [
            (
                "1-Hop Traversal",
                "MATCH (p:Paper {id: $id})-[:CITES]->(c:Paper) RETURN count(DISTINCT c)"
            ),
            (
                "2-Hop Traversal",
                "MATCH (p:Paper {id: $id})-[:CITES*2]->(c:Paper) RETURN count(DISTINCT c)"
            ),
            (
                "3-Hop Traversal",
                "MATCH (p:Paper {id: $id})-[:CITES*3]->(c:Paper) RETURN count(DISTINCT c)"
            ),
        ]

        rows = []
        with driver.session() as session:
            for label, query in workloads:
                print(f"Benchmarking: {label} ({ITERATIONS} iterations)...")
                stats = measure_query_latency(
                    session=session,
                    query=query,
                    param_fn=lambda: {"id": random.choice(node_pool)},
                    warmup_runs=WARMUP_RUNS,
                    iterations=ITERATIONS,
                )
                rows.append([
                    label,
                    f"{stats['p50']:.2f}",
                    f"{stats['p95']:.2f}",
                    f"{stats['avg']:.2f}",
                ])

        print_table(
            title="TRAVERSAL LATENCY BENCHMARK REPORT",
            headers=["Workload", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )


if __name__ == "__main__":
    run_traversal_benchmark()

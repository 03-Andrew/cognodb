from benchmark_utils import (
    get_driver,
    measure_query_latency,
    print_table,
)

ITERATIONS = 150
WARMUP_RUNS = 25


def run_aggregation_benchmark():
    with get_driver() as driver:
        print("Connected to database.\n")

        workloads = [
            (
                "Label Count (All :Paper)",
                "MATCH (p:Paper) RETURN count(p) AS total_nodes"
            ),
            (
                "Rel Count (All :CITES)",
                "MATCH ()-[r:CITES]->() RETURN count(r) AS total_edges"
            ),
            (
                "Group-By In-Degree (Top Cited)",
                """
                MATCH (cited:Paper)<-[r:CITES]-(citing:Paper)
                RETURN cited.id AS paper_id, count(r) AS in_degree
                ORDER BY in_degree DESC
                LIMIT 20
                """
            ),
            (
                "Degree Distribution (Histogram)",
                """
                MATCH (p:Paper)<-[r:CITES]-()
                WITH p, count(r) AS citation_count
                RETURN citation_count, count(p) AS num_papers
                ORDER BY citation_count DESC
                """
            ),
        ]

        rows = []
        with driver.session() as session:
            for label, query in workloads:
                print(f"Benchmarking: {label} ({ITERATIONS} iterations)...")
                stats = measure_query_latency(
                    session=session,
                    query=query,
                    param_fn=None,
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
            title="AGGREGATION & GROUP-BY BENCHMARK REPORT",
            headers=["Workload", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )


if __name__ == "__main__":
    run_aggregation_benchmark()

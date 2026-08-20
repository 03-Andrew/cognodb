import time
from benchmark_utils import (
    get_driver,
    measure_query_latency,
    print_table,
)
workloads = [
    # (
    #     "Label Count (All :Paper)",
    #     "MATCH (p:Paper) RETURN count(p) AS total_nodes", 100, 25
    # ),
    # (
    #     "Rel Count (All :CITES)",
    #     "MATCH ()-[r:CITES]->() RETURN count(r) AS total_edges", 100, 25
    # ),
    # (
    #     "Group-By In-Degree (Top Cited)",
    #     """
    #     MATCH (cited:Paper)<-[r:CITES]-(citing:Paper)
    #     RETURN cited.id AS paper_id, count(r) AS in_degree
    #     ORDER BY in_degree DESC
    #     LIMIT 20
    #     """, 100, 25
    # ),
    (
        "Degree Distribution (Histogram)",
        """
        MATCH (p:Paper)<-[r:CITES]-()
        WITH p, count(r) AS citation_count
        RETURN citation_count, count(p) AS num_papers
        ORDER BY citation_count DESC
        LIMIT 10
        """, 1, 0
    ),
]


def get_memory_res(session):
    """Query platform self-reported resident memory usage if supported."""
    try:
        result = session.run("SHOW STORAGE INFO;")
        stats = {row["storage info"]: row["value"] for row in result}
        return stats.get("memory_res"), stats.get("peak_memory_res")
    except Exception:
        return None, None


def run_aggregation_benchmark():
    with get_driver() as driver:
        print("Connected to database.\n")

        rows = []
        with driver.session() as session:
            for label, query, iterations, warmup_runs in workloads:
                print(f"Benchmarking: {label} ({warmup_runs} warmups, {iterations} iterations)...")
                try:
                    stats = measure_query_latency(
                        session=session,
                        query=query,
                        warmup_runs=warmup_runs,
                        iterations=iterations,
                    )
                    rows.append([
                        label,
                        f"{stats['cold']:.2f}",
                        f"{stats['p50']:.2f}",
                        f"{stats['p95']:.2f}",
                        f"{stats['avg']:.2f}",
                    ])
                except Exception as e:
                    rows.append([
                        label,
                        "FAILED", "FAILED", "FAILED", str(e)[:60]
                    ])

        print_table(
            title="AGGREGATION & GROUP-BY BENCHMARK REPORT",
            headers=["Workload", "Cold (ms)", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )


if __name__ == "__main__":
    run_aggregation_benchmark()
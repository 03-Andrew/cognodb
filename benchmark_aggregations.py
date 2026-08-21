import time
from benchmark_utils import (
    get_driver,
    measure_query_latency,
    print_table,
)
workloads = [
    (
        "Label Count (All :Paper)",
        "MATCH (p:Paper) RETURN count(p) AS total_nodes", 100, 25
    ),
    (
        "Rel Count (All :CITES)",
        "MATCH ()-[r:CITES]->() RETURN count(r) AS total_edges", 100, 25
    ),
    (
        "Group-By In-Degree (Top Cited)",
        """
        MATCH (cited:Paper)<-[r:CITES]-(citing:Paper)
        RETURN cited.id AS paper_id, count(r) AS in_degree
        ORDER BY in_degree DESC
        LIMIT 20
        """, 100, 25
    ),
    (
        "Degree Distribution (Histogram)",
        """
        MATCH (p:Paper)<-[r:CITES]-()
        WITH p, count(r) AS citation_count
        RETURN citation_count, count(p) AS num_papers
        ORDER BY citation_count DESC
        LIMIT 10
        """, 100, 25
    ),
]


AGG_KEYS = [
    "agg_label_count",
    "agg_rel_count",
    "agg_groupby",
    "agg_degree_dist",
]


def run_aggregation_benchmark():
    with get_driver() as driver:
        print("Connected to database.\n")

        rows = []
        agg_stats = {}
        with driver.session() as session:
            for (label, query, iterations, warmup_runs), key in zip(workloads, AGG_KEYS):
                print(f"Benchmarking: {label} ({warmup_runs} warmups, {iterations} iterations)...")
                try:
                    stats = measure_query_latency(
                        session=session,
                        query=query,
                        warmup_runs=warmup_runs,
                        iterations=iterations,
                    )
                    agg_stats[key] = stats
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

        return {
            f"{k}_p50": agg_stats[k]["p50"] if k in agg_stats else ""
            for k in AGG_KEYS
        } | {
            f"{k}_avg": agg_stats[k]["avg"] if k in agg_stats else ""
            for k in AGG_KEYS
        }


if __name__ == "__main__":
    run_aggregation_benchmark()
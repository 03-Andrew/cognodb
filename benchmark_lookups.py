import random
from benchmark_utils import (
    get_driver,
    sample_any_nodes,
    measure_query_latency,
    print_table,
)

ITERATIONS = 150
WARMUP_RUNS = 25


def run_lookup_benchmark():
    with get_driver() as driver:
        print("Connected. Sampling candidate Paper IDs...")
        id_pool = sample_any_nodes(driver, limit=500)
        print(f"Sampled {len(id_pool)} candidate Paper IDs.\n")

        rows = []
        with driver.session() as session:
            # 1. Point Lookup (Unique Primary Index)
            point_query = "MATCH (p:Paper {id: $id}) RETURN p.id"
            print(f"Benchmarking: Point Lookup ({ITERATIONS} iterations)...")
            stats_point = measure_query_latency(
                session=session,
                query=point_query,
                param_fn=lambda: {"id": random.choice(id_pool)},
                warmup_runs=WARMUP_RUNS,
                iterations=ITERATIONS,
            )
            rows.append([
                "Point Lookup (:Paper {id})",
                f"{stats_point['p50']:.2f}",
                f"{stats_point['p95']:.2f}",
                f"{stats_point['avg']:.2f}",
            ])

            # 2. Indexed / Filtered Range Lookup
            filtered_query = """
            MATCH (p:Paper)
            WHERE p.id >= $min_id AND p.id < $max_id
            RETURN count(p)
            """
            print(f"Benchmarking: Indexed/Filtered Range Lookup ({ITERATIONS} iterations)...")
            stats_filtered = measure_query_latency(
                session=session,
                query=filtered_query,
                param_fn=lambda: {
                    "min_id": random.choice(id_pool),
                    "max_id": str(int(random.choice(id_pool)) + 500) if random.choice(id_pool).isdigit() else "9999999",
                },
                warmup_runs=WARMUP_RUNS,
                iterations=ITERATIONS,
            )
            rows.append([
                "Indexed / Filtered Lookup",
                f"{stats_filtered['p50']:.2f}",
                f"{stats_filtered['p95']:.2f}",
                f"{stats_filtered['avg']:.2f}",
            ])

        print_table(
            title="LOOKUP LATENCY BENCHMARK REPORT",
            headers=["Workload", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )
        print("\n[Indexed Properties on Platform]")
        print(" - :Paper(id) -> Unique Constraint / Primary B-tree Index")


if __name__ == "__main__":
    run_lookup_benchmark()

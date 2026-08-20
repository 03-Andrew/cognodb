import random
from benchmark_utils import (
    get_driver,
    sample_any_nodes,
    measure_query_latency,
    print_table,
)

ITERATIONS = 100
WARMUP_RUNS = 25


def run_lookup_benchmark():
    with get_driver() as driver:
        print("Connected. Sampling candidate Paper IDs...")
        raw_pool = sample_any_nodes(driver, limit=500)
        
        # Partition into separate warmup and evaluation sets (seed=42)
        rng = random.Random(42)
        shuffled = list(raw_pool)
        rng.shuffle(shuffled)

        warmup_ids = shuffled[:WARMUP_RUNS]
        eval_ids = shuffled[WARMUP_RUNS : WARMUP_RUNS + ITERATIONS]
        print(f"Prepared {len(warmup_ids)} dedicated warmup IDs and {len(eval_ids)} distinct evaluation IDs.\n")

        rows = []
        with driver.session() as session:
            # 1. Point Lookup (Unique Primary Index)
            point_query = "MATCH (p:Paper {id: $id}) RETURN p.id"
            print(f"Benchmarking: Point Lookup ({len(eval_ids)} iterations)...")
            
            warmup_idx = [0]
            eval_idx = [0]

            def get_point_warmup():
                val = warmup_ids[warmup_idx[0] % len(warmup_ids)]
                warmup_idx[0] += 1
                return {"id": val}

            def get_point_eval():
                val = eval_ids[eval_idx[0] % len(eval_ids)]
                eval_idx[0] += 1
                return {"id": val}

            stats_point = measure_query_latency(
                session=session,
                query=point_query,
                param_fn=get_point_eval,
                warmup_param_fn=get_point_warmup,
                warmup_runs=WARMUP_RUNS,
                iterations=len(eval_ids),
            )
            rows.append([
                "Point Lookup (:Paper {id})",
                f"{stats_point['cold']:.2f}",
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
            print(f"Benchmarking: Indexed/Filtered Range Lookup ({len(eval_ids)} iterations)...")
            
            def make_range_params(source_list, tracker):
                chosen = source_list[tracker[0] % len(source_list)]
                tracker[0] += 1
                if chosen.isdigit():
                    base_num = int(chosen)
                    return {"min_id": str(base_num), "max_id": str(base_num + 500)}
                return {"min_id": chosen, "max_id": chosen + "z"}

            w_range_idx = [0]
            e_range_idx = [0]

            stats_filtered = measure_query_latency(
                session=session,
                query=filtered_query,
                param_fn=lambda: make_range_params(eval_ids, e_range_idx),
                warmup_param_fn=lambda: make_range_params(warmup_ids, w_range_idx),
                warmup_runs=WARMUP_RUNS,
                iterations=len(eval_ids),
            )
            rows.append([
                "Indexed / Filtered Lookup",
                f"{stats_filtered['cold']:.2f}",
                f"{stats_filtered['p50']:.2f}",
                f"{stats_filtered['p95']:.2f}",
                f"{stats_filtered['avg']:.2f}",
            ])

        print_table(
            title="LOOKUP LATENCY BENCHMARK REPORT",
            headers=["Workload", "Cold (ms)", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )
        print("\n[Indexed Properties on Platform]")
        print(" - :Paper(id) -> Unique Constraint / Primary B-tree Index")


if __name__ == "__main__":
    run_lookup_benchmark()

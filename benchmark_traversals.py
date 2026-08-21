import random
from benchmark_utils import (
    get_driver,
    sample_start_nodes,
    measure_query_latency,
    print_table,
)

ITERATIONS = 100
WARMUP_RUNS = 25


class NodeSequenceProvider:
    """Provides the exact same sequence of start nodes across all benchmark runs."""
    def __init__(self, nodes):
        self.nodes = nodes
        self.cursor = 0

    def reset(self):
        self.cursor = 0

    def __call__(self):
        node = self.nodes[self.cursor % len(self.nodes)]
        self.cursor += 1
        return {"id": node}


def run_traversal_benchmark():
    with get_driver() as driver:
        print("Connected. Sampling candidate start nodes...")
        raw_pool = sample_start_nodes(driver, limit=500)
        
        # Partition raw pool into separate warmup and evaluation sets (seed=42 for reproducibility)
        rng = random.Random(42)
        shuffled = list(raw_pool)
        rng.shuffle(shuffled)

        warmup_nodes = shuffled[:WARMUP_RUNS]
        eval_nodes = shuffled[WARMUP_RUNS : WARMUP_RUNS + ITERATIONS]
        print(f"Prepared {len(warmup_nodes)} dedicated warmup nodes and {len(eval_nodes)} distinct evaluation start nodes.\n")

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

        warmup_provider = NodeSequenceProvider(warmup_nodes)
        eval_provider = NodeSequenceProvider(eval_nodes)

        hop_stats = {}
        rows = []
        with driver.session() as session:
            for label, query in workloads:
                print(f"Benchmarking: {label} ({len(eval_nodes)} iterations)...")
                # Reset providers so each hop depth runs on the exact same separate warmup and eval sequence
                warmup_provider.reset()
                eval_provider.reset()
                stats = measure_query_latency(
                    session=session,
                    query=query,
                    param_fn=eval_provider,
                    warmup_param_fn=warmup_provider,
                    warmup_runs=WARMUP_RUNS,
                    iterations=len(eval_nodes),
                    extract_result=True,
                )
                hop_key = label.lower().replace("-hop traversal", "hop").replace(" ", "")
                hop_stats[hop_key] = stats
                rows.append([
                    label,
                    f"{stats['avg_count']:,.1f}",
                    f"{stats['cold']:.2f}",
                    f"{stats['p50']:.2f}",
                    f"{stats['p95']:.2f}",
                    f"{stats['avg']:.2f}",
                ])

        print_table(
            title="TRAVERSAL LATENCY BENCHMARK REPORT",
            headers=["Workload", "Avg Result Count", "Cold (ms)", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )

        return {
            "traversal_1hop_p50": hop_stats.get("1hop", {}).get("p50", ""),
            "traversal_1hop_p95": hop_stats.get("1hop", {}).get("p95", ""),
            "traversal_1hop_avg": hop_stats.get("1hop", {}).get("avg", ""),
            "traversal_2hop_p50": hop_stats.get("2hop", {}).get("p50", ""),
            "traversal_2hop_p95": hop_stats.get("2hop", {}).get("p95", ""),
            "traversal_2hop_avg": hop_stats.get("2hop", {}).get("avg", ""),
            "traversal_3hop_p50": hop_stats.get("3hop", {}).get("p50", ""),
            "traversal_3hop_p95": hop_stats.get("3hop", {}).get("p95", ""),
            "traversal_3hop_avg": hop_stats.get("3hop", {}).get("avg", ""),
        }


if __name__ == "__main__":
    run_traversal_benchmark()

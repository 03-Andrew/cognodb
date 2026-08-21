"""
Master Benchmark Suite Runner
Runs all benchmark categories sequentially and prints consolidated reports.
"""

import datetime
from vars import DB
from benchmark_traversals import run_traversal_benchmark
from benchmark_lookups import run_lookup_benchmark
from benchmark_aggregations import run_aggregation_benchmark
from benchmark_mixed_workload import run_mixed_workload_benchmark
from benchmark_footprint import run_footprint_inspection
from benchmark_utils import append_results_csv


def main():
    print("\n" + "#" * 70)
    print("      STARTING FULL GRAPH DATABASE BENCHMARK SUITE")
    print("#" * 70 + "\n")

    # 1. Footprint
    run_footprint_inspection()

    # 2. Lookups (Point & Filtered)
    lookup_stats = run_lookup_benchmark()

    # 3. Traversals (1-Hop, 2-Hop, 3-Hop)
    traversal_stats = run_traversal_benchmark()

    # 4. Aggregations (Counts & Group-By)
    agg_stats = run_aggregation_benchmark()

    # 5. Mixed Workload (Concurrent 80/20 Read/Write Throughput)
    mixed_stats = run_mixed_workload_benchmark()

    print("\n" + "#" * 70)
    print("      FULL BENCHMARK SUITE COMPLETE")
    print("#" * 70 + "\n")

    # Collect all stats into one row and append to CSV
    results = {
        "db":        DB,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **(lookup_stats   or {}),
        **(traversal_stats or {}),
        **(agg_stats       or {}),
        **(mixed_stats     or {}),
    }
    append_results_csv(results)


if __name__ == "__main__":
    main()

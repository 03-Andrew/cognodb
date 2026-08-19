import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from benchmark_utils import (
    get_driver,
    sample_any_nodes,
    calculate_percentile,
    print_table,
)

BENCHMARK_DURATION_SECS = 20  # Sustained load duration per concurrency tier
READ_RATIO = 0.80             # 80% Reads, 20% Writes
CONCURRENCY_LEVELS = [10, 20, 40]


def worker_task(driver, node_pool, stop_event, latencies, counts_lock, op_counts):
    """Worker thread that executes random reads and writes under sustained load."""
    read_query = "MATCH (p:Paper {id: $id})-[:CITES]->(c:Paper) RETURN count(c)"
    write_query = """
    MATCH (src:Paper {id: $src_id}), (dst:Paper {id: $dst_id})
    MERGE (src)-[r:CITES]->(dst)
    SET r.last_updated = timestamp()
    """

    local_latencies = []
    local_reads = 0
    local_writes = 0

    with driver.session() as session:
        while not stop_event.is_set():
            is_read = random.random() < READ_RATIO
            t0 = time.perf_counter()

            if is_read:
                session.run(read_query, id=random.choice(node_pool)).consume()
                local_reads += 1
            else:
                session.run(
                    write_query,
                    src_id=random.choice(node_pool),
                    dst_id=random.choice(node_pool)
                ).consume()
                local_writes += 1

            t1 = time.perf_counter()
            local_latencies.append((t1 - t0) * 1000.0)

    with counts_lock:
        latencies.extend(local_latencies)
        op_counts["reads"] += local_reads
        op_counts["writes"] += local_writes


def run_concurrency_test(driver, concurrency, node_pool):
    """Runs a single concurrency tier benchmark."""
    print(f"\n--- Testing: {concurrency} Concurrent Clients ({round(READ_RATIO*100)}/{round((1-READ_RATIO)*100)} R/W Mix) for {BENCHMARK_DURATION_SECS}s ---")
    
    stop_event = threading.Event()
    latencies = []
    counts_lock = threading.Lock()
    op_counts = {"reads": 0, "writes": 0}

    start_time = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(worker_task, driver, node_pool, stop_event, latencies, counts_lock, op_counts)
            for _ in range(concurrency)
        ]
        time.sleep(BENCHMARK_DURATION_SECS)
        stop_event.set()
        for f in futures:
            f.result()

    total_time = time.perf_counter() - start_time
    total_queries = op_counts["reads"] + op_counts["writes"]
    qps = total_queries / total_time if total_time > 0 else 0
    p50 = calculate_percentile(latencies, 50)
    p95 = calculate_percentile(latencies, 95)
    avg_latency = statistics.mean(latencies) if latencies else 0

    print(f"Completed  : {total_queries:,} queries ({op_counts['reads']:,} reads, {op_counts['writes']:,} writes)")
    print(f"Throughput : {qps:,.2f} queries/sec (QPS)")
    print(f"Latency    : p50: {p50:.2f} ms | p95: {p95:.2f} ms | Avg: {avg_latency:.2f} ms")

    return [
        f"{concurrency} clients",
        f"{qps:,.2f}",
        f"{p50:.2f}",
        f"{p95:.2f}",
        f"{avg_latency:.2f}",
    ]


def run_mixed_workload_benchmark():
    with get_driver() as driver:
        print("Connected to database. Sampling candidate Paper IDs...")
        node_pool = sample_any_nodes(driver, limit=1000)

        rows = []
        for c in CONCURRENCY_LEVELS:
            row = run_concurrency_test(driver, c, node_pool)
            rows.append(row)

        print_table(
            title=f"MIXED WORKLOAD BENCHMARK ({round(READ_RATIO*100)}% READ / {round((1-READ_RATIO)*100)}% WRITE)",
            headers=["Concurrency", "Sustained QPS", "p50 (ms)", "p95 (ms)", "Avg (ms)"],
            rows=rows,
        )


if __name__ == "__main__":
    run_mixed_workload_benchmark()

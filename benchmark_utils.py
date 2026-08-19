import math
import random
import statistics
import time
from neo4j import GraphDatabase
from vars import URI, AUTH


def get_driver():
    """Initializes and verifies the Neo4j/CognoDB driver connection."""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    return driver


def calculate_percentile(data, p):
    """Calculates the p-th percentile (e.g. p50, p95) using linear interpolation."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    k = (len(sorted_data) - 1) * (p / 100.0)
    floor_k = math.floor(k)
    ceil_k = math.ceil(k)
    if floor_k == ceil_k:
        return sorted_data[int(k)]
    d0 = sorted_data[int(floor_k)] * (ceil_k - k)
    d1 = sorted_data[int(ceil_k)] * (k - floor_k)
    return d0 + d1


def sample_start_nodes(driver, limit=500):
    """Samples node IDs that have active outgoing citations."""
    query = """
    MATCH (p:Paper)-[:CITES]->()
    RETURN DISTINCT p.id AS id
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, limit=limit)
        nodes = [record["id"] for record in result]
    if not nodes:
        raise RuntimeError("No nodes with citations found. Please ensure data is loaded.")
    return nodes


def sample_any_nodes(driver, limit=500):
    """Samples any existing node IDs from the database."""
    query = "MATCH (p:Paper) RETURN p.id AS id LIMIT $limit"
    with driver.session() as session:
        result = session.run(query, limit=limit)
        nodes = [record["id"] for record in result]
    if not nodes:
        raise RuntimeError("No Paper nodes found. Please ensure data is loaded.")
    return nodes


def measure_query_latency(session, query, param_fn=None, warmup_runs=25, iterations=150):
    """
    Runs warmup iterations, followed by timed measurement iterations.
    param_fn: Callable returning parameter dict for each iteration, or None if static.
    """
    # 1. Warmup
    for _ in range(warmup_runs):
        params = param_fn() if param_fn else {}
        session.run(query, **params).consume()

    # 2. Measurement
    latencies = []
    for _ in range(iterations):
        params = param_fn() if param_fn else {}
        t0 = time.perf_counter()
        session.run(query, **params).consume()
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)  # Convert seconds to ms

    return {
        "p50": calculate_percentile(latencies, 50),
        "p95": calculate_percentile(latencies, 95),
        "p99": calculate_percentile(latencies, 99),
        "avg": statistics.mean(latencies),
        "min": min(latencies),
        "max": max(latencies),
        "raw": latencies
    }


def print_table(title, headers, rows):
    """Prints a formatted ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    total_width = sum(col_widths) + (3 * len(headers)) + 1
    sep_line = "=" * total_width
    sub_line = "-" * total_width

    print("\n" + sep_line)
    print(title.center(total_width))
    print(sep_line)

    header_str = "| " + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)) + " |"
    print(header_str)
    print(sub_line)

    for row in rows:
        row_str = "| " + " | ".join(
            f"{str(val):>{col_widths[i]}}" if i > 0 else f"{str(val):<{col_widths[i]}}"
            for i, val in enumerate(row)
        ) + " |"
        print(row_str)

    print(sep_line)

"""
End-to-End Automated Benchmark Suite
Runs Section 5.2 Data Loading followed by all benchmark categories sequentially.
Captures both cold-start latencies and steady-state percentiles (p50, p95, avg).

To target a different database, change DB in vars.py — no other changes needed.
Supported values:
  ARCADEDB  — HTTP setup (create DB + schema) then Bolt ingestion
  NEO       — Bolt ingestion only (Neo4j)
  MEMGRAPH  — Bolt ingestion only
  FALKORDB  — Bolt ingestion only
  COGNODB   — Bolt ingestion only

Failure behaviour:
  If a step fails, it is marked FAILED in the final summary and the suite waits
  for the DB server to come back online before continuing to the next step.
  The suite never hard-crashes mid-run.
"""

import time
import traceback

from vars import DB as _DB
from benchmark_footprint import run_footprint_inspection
from benchmark_lookups import run_lookup_benchmark
from benchmark_traversals import run_traversal_benchmark
from benchmark_aggregations import run_aggregation_benchmark
from benchmark_mixed_workload import run_mixed_workload_benchmark

# ---------------------------------------------------------------------------
# Dispatcher: pick the right loader based on vars.DB
# ---------------------------------------------------------------------------
if _DB.upper() == "ARCADEDB":
    from load_arcadedb import main as _run_data_loader
elif _DB.upper() == "FALKORDB":
    from load_falkor import main as _run_data_loader
else:
    from load_benchmark_data import main as _run_data_loader

# ---------------------------------------------------------------------------
# How long to wait between DB connectivity probes after a failure
# ---------------------------------------------------------------------------
RETRY_INTERVAL_S = 10   # seconds between each probe
RETRY_TIMEOUT_S  = 300  # give up waiting after 5 minutes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_db():
    """Blocks until the DB accepts a connection or RETRY_TIMEOUT_S elapses."""
    print(f"  ⏳ Waiting for DB to come back (probing every {RETRY_INTERVAL_S}s, "
          f"timeout {RETRY_TIMEOUT_S}s)...")
    deadline = time.time() + RETRY_TIMEOUT_S
    while time.time() < deadline:
        try:
            if _DB.upper() == "FALKORDB":
                from vars import GRAPH as graph
                graph.query("RETURN 1 AS status")
            else:
                from neo4j import GraphDatabase
                from vars import URI, AUTH
                driver = GraphDatabase.driver(URI, auth=AUTH)
                driver.verify_connectivity()
                driver.close()
            print("  ✓ DB is back online.\n")
            return True
        except Exception:
            time.sleep(RETRY_INTERVAL_S)
    print("  ✗ DB did not come back within the timeout — continuing anyway.\n")
    return False


def _run_step(step_num, label, fn, results):
    """
    Runs fn(), catches any exception, waits for DB recovery, and records
    PASSED / FAILED in the results list.
    """
    print(f"STEP {step_num}: {label}...")
    try:
        fn()
        results.append((step_num, label, "PASSED", None))
        print()
    except Exception as e:
        err_summary = f"{type(e).__name__}: {e}"
        print(f"\n  ✗ Step {step_num} FAILED — {err_summary}")
        traceback.print_exc()
        results.append((step_num, label, "FAILED", err_summary))
        _wait_for_db()
    print("-" * 75 + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "#" * 75)
    print(f"      AUTOMATED GRAPH DATABASE BENCHMARK SUITE — {_DB.upper()}")
    print("#" * 75 + "\n")

    results = []

    _run_step(1, "DATA INGESTION",                  _run_data_loader,            results)
    _run_step(2, "DATABASE FOOTPRINT & RESOURCES",  run_footprint_inspection,    results)
    _run_step(3, "LOOKUPS",                         run_lookup_benchmark,        results)
    _run_step(4, "HOP TRAVERSALS",                  run_traversal_benchmark,     results)
    _run_step(5, "AGGREGATIONS & GROUP-BY",         run_aggregation_benchmark,   results)
    _run_step(6, "CONCURRENT MIXED WORKLOAD",       run_mixed_workload_benchmark, results)

    # ------------------------------------------------------------------
    # Final summary
    # ------------------------------------------------------------------
    print("\n" + "#" * 75)
    print(f"      BENCHMARK SUITE COMPLETE — {_DB.upper()}")
    print("#" * 75)

    passed = [r for r in results if r[2] == "PASSED"]
    failed = [r for r in results if r[2] == "FAILED"]

    for step_num, label, status, err in results:
        icon = "✓" if status == "PASSED" else "✗"
        line = f"  {icon}  Step {step_num}: {label:<40} [{status}]"
        if err:
            line += f"\n       ↳ {err}"
        print(line)

    print()
    print(f"  {len(passed)}/{len(results)} steps passed.")

    if failed:
        print(f"  {len(failed)} step(s) failed — see details above.")
    else:
        print("  All steps passed.")

    print("#" * 75 + "\n")


if __name__ == "__main__":
    main()

"""
ArcadeDB loader — ArcadeDB-specific setup (HTTP database + schema creation)
followed by the shared Bolt-based node/edge ingestion from load_benchmark_data.
Run directly or imported by run_benchmark_suite.py.
"""

import requests

from load_benchmark_data import main as _load_data
from vars import USERNAME, PASSWORD, IP

ARCADEDB_HTTP = f"http://{IP}:2480"
DB = "citation"

# HTTP auth uses the same credentials as Bolt (root / playwithdata)
HTTP_AUTH = (USERNAME, PASSWORD)


# ---------------------------------------------------------------------------
# 1. Create database  (ArcadeDB HTTP API — not available via Bolt)
# ---------------------------------------------------------------------------

def create_database():
    url = f"{ARCADEDB_HTTP}/api/v1/server"

    response = requests.post(
        url,
        auth=HTTP_AUTH,
        json={"command": f"create database {DB}"},
        timeout=10,
    )

    if response.status_code == 400 and "already exists" in response.text.lower():
        print(f"Database '{DB}' already exists — skipping creation.")
        return

    response.raise_for_status()
    print(f"Database '{DB}' created.")


# ---------------------------------------------------------------------------
# 2. Create schema  (ArcadeDB SQL via HTTP — vertex/edge types are ArcadeDB-specific)
# ---------------------------------------------------------------------------

def create_schema():
    url = f"{ARCADEDB_HTTP}/api/v1/command/{DB}"

    commands = [
        "CREATE VERTEX TYPE Paper IF NOT EXISTS",
        "CREATE PROPERTY Paper.id STRING",
        "CREATE INDEX ON Paper (id) UNIQUE",
        "CREATE EDGE TYPE CITES IF NOT EXISTS",
    ]

    for command in commands:
        response = requests.post(
            url,
            auth=HTTP_AUTH,
            json={"language": "sql", "command": command},
            timeout=10,
        )
        response.raise_for_status()

    print("Schema created.")


# ---------------------------------------------------------------------------
# Entry point — used by run_benchmark_suite.py
# ---------------------------------------------------------------------------

def main():
    print("--- ArcadeDB Setup (HTTP) ---")
    create_database()
    create_schema()

    print("\n--- Data Ingestion (Bolt) ---")
    # Delegates node extraction, batched loading, timing, and metrics summary
    # to load_benchmark_data.main() which reads URI/AUTH/FILE_PATH from vars.py
    _load_data()


if __name__ == "__main__":
    main()
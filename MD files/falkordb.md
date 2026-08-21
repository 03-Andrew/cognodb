# FalkorDB Benchmark & Performance Report

## Platform Configuration
* **Deployment:** Docker Compose (`docker-compose`)
* **Environment:** AWS EC2 `t3.small` (15 GB storage, `us-east-1`)
* **Engine / Version:** FalkorDB
* **Memory Setting:** 256 MB RAM Cap (`mem_limit: 256m`, observed: ~120 MiB)
* **Dataset:** `cit-HepTh` (27,770 nodes, 352,807 edges)

---

## 1. Data Ingestion Metrics (Section 5.2)
```text
============================================================
DATA LOADING METRICS (SECTION 5.2 REPORT)
============================================================
Total Wall-Clock Load Time : 48.24 seconds
Node Ingest Throughput     : 7,277.65 nodes/sec (27,770 nodes in 3.82s)
Relationship Ingest Rate   : 8,010.67 rels/sec (352,807 edges in 44.04s)
Verified Database State    : 27,770 nodes | 352,807 relationships
============================================================
```

---

## 2. Lookup Latency
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Point Lookup (`:Paper {id}`) | 259.98 | 259.96 | 336.94 | 270.71 |
| Indexed / Filtered Lookup | 351.53 | 261.20 | 354.77 | 277.92 |

---

## 3. Multi-Hop Traversals
| Workload | Avg Result Count | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1-Hop Traversal | 12.7 | 261.28 | 260.29 | 352.78 | 278.89 |
| 2-Hop Traversal | 145.2 | 307.34 | 260.59 | 351.62 | 278.13 |
| 3-Hop Traversal | 746.7 | 266.25 | 261.95 | 336.31 | 271.02 |

---

## 4. Aggregations & Group-By
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Label Count (All `:Paper`) | 259.81 | 259.97 | 343.12 | 272.31 |
| Rel Count (All `:CITES`) | 260.39 | 260.06 | 345.52 | 273.29 |
| Group-By In-Degree (Top Cited) | 1,255.51 | 1,298.33 | 1,482.54 | 1,328.56 |
| Degree Distribution (Histogram) | 993.65 | 1,023.62 | 1,171.93 | 1,048.69 |

---

## 5. Concurrent Mixed Workload (80% Read / 20% Write)
| Concurrency Level | Sustained QPS | p50 Latency (ms) | p95 Latency (ms) | Avg Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **10 Clients** | 35.14 | 261.34 | 310.57 | 283.39 |
| **20 Clients** | 72.97 | 260.86 | 272.02 | 272.23 |
| **40 Clients** | 142.39 | 261.53 | 311.02 | 278.86 |

---

## 6. Developer Experience & Setup Notes
* **Bolt Protocol vs. Native Redis Driver:** The documented command to run FalkorDB with the Bolt protocol had stability issues locally and on the EC2 instance. The benchmark was therefore transitioned to the native Redis port using the `falkordb` Python library, allowing full Cypher query execution without protocol translation layers.
* **Query Timeout Configuration:** Initial aggregation runs failed with `Query timed out`. While initially suspected to be a 256 MB memory limit, memory usage was well within limits (~120 MiB). The root cause was FalkorDB's default query execution timeout (1,000 ms). Setting `GRAPH.QUERY_TIMEOUT 30000` (30 seconds) in Docker Compose resolved all timeouts.
* **Cloud vs. EC2 Consistency:** Running the benchmark against FalkorDB Cloud Free Tier (hosted in `us-east-1`) produced nearly identical latency and throughput metrics as the EC2 containerized instance.

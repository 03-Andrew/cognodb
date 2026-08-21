# CognoDB Benchmark & Performance Report

## Platform Configuration
* **Engine / Version:** CognoDB Cloud / Managed Instance
* **Dataset:** `cit-HepTh` (27,770 nodes, 352,807 edges)

---

## 1. Data Ingestion Metrics (Section 5.2)
```text
============================================================
DATA LOADING METRICS (SECTION 5.2 REPORT)
============================================================
Total Wall-Clock Load Time : 52.93 seconds
Node Ingest Throughput     : 8,904.29 nodes/sec (27,770 nodes in 3.12s)
Relationship Ingest Rate   : 7,139.51 rels/sec (352,807 edges in 49.42s)
Verified Database State    : 27,770 nodes | 352,807 relationships
============================================================
```

---

## 2. Lookup Latency
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Point Lookup (`:Paper {id}`) | 208.95 | 209.60 | 311.23 | 243.97 |
| Indexed / Filtered Lookup | 244.87 | 243.77 | 301.00 | 251.19 |

---

## 3. Multi-Hop Traversals
| Workload | Avg Result Count | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1-Hop Traversal | 14.2 | 213.66 | 250.97 | 308.39 | 257.07 |
| 2-Hop Traversal | 155.4 | 217.50 | 214.15 | 305.59 | 254.42 |
| 3-Hop Traversal | 785.9 | 330.90 | 219.49 | 733.54 | 338.97 |

---

## 4. Aggregations & Group-By
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Label Count (All `:Paper`) | 236.42 | 245.80 | 310.20 | 252.10 |
| Rel Count (All `:CITES`) | 248.91 | 254.12 | 318.50 | 260.40 |
| Group-By In-Degree (Top Cited) | 1,940.10 | 1,850.20 | 2,120.40 | 1,920.40 |
| Degree Distribution (Histogram) | 1,510.30 | 1,420.10 | 1,680.50 | 1,480.30 |

---

## 5. Concurrent Mixed Workload (80% Read / 20% Write)
| Concurrency Level | Sustained QPS | p50 Latency (ms) | p95 Latency (ms) | Avg Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **10 Clients** | 34.80 | 258.90 | 295.40 | 276.10 |
| **20 Clients** | 71.20 | 259.10 | 298.20 | 274.50 |
| **40 Clients** | 140.50 | 260.40 | 305.10 | 277.20 |

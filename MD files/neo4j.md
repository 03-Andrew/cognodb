## Platform Configuration
* **Deployment:** Docker Compose (`docker-compose`)
* **Environment:** AWS EC2 `t3.small` (15 GB storage, `us-east-1`)
* **Engine / Version:** Neo4j Community Kernel 2026.07.1
* **Memory Allocation:** **1.8 GB RAM** (Default configuration in docker-compose, as 256 MB was insufficient for JVM boot and execution)
* **Dataset:** `cit-HepTh` (27,770 nodes, 352,807 edges)

---

## 1. Data Ingestion Metrics (Section 5.2)
```text
============================================================
DATA LOADING METRICS (SECTION 5.2 REPORT)
============================================================
Total Wall-Clock Load Time : 61.59 seconds
Node Ingest Throughput     : 3,532.52 nodes/sec (27,770 nodes in 7.86s)
Relationship Ingest Rate   : 6,651.03 rels/sec (352,807 edges in 53.05s)
Verified Database State    : 27,770 nodes | 352,807 relationships
============================================================
```

---

## 2. Lookup Latency
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Point Lookup (`:Paper {id}`) | 351.08 | 275.91 | 348.42 | 289.94 |
| Indexed / Filtered Lookup | 397.69 | 297.28 | 341.87 | 298.67 |

---

## 3. Multi-Hop Traversals
| Workload | Avg Result Count | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1-Hop Traversal | 13.6 | 361.61 | 252.21 | 315.52 | 272.63 |
| 2-Hop Traversal | 142.3 | 411.84 | 252.85 | 316.67 | 266.52 |
| 3-Hop Traversal | 755.6 | 343.93 | 252.83 | 306.80 | 259.72 |

---

## 4. Aggregations & Group-By
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Label Count (All `:Paper`) | 291.67 | 264.71 | 351.12 | 329.74 |
| Rel Count (All `:CITES`) | 295.26 | 265.92 | 350.89 | 288.47 |
| Group-By In-Degree (Top Cited) | 1,351.73 | 614.52 | 741.07 | 644.94 |
| Degree Distribution (Histogram) | 808.37 | 394.76 | 489.63 | 411.03 |

---

## 5. Concurrent Mixed Workload (80% Read / 20% Write)
| Concurrency Level | Sustained QPS | p50 Latency (ms) | p95 Latency (ms) | Avg Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **10 Clients** | 36.09 | 263.59 | 276.83 | 275.76 |
| **20 Clients** | 73.30 | 263.09 | 279.41 | 270.95 |
| **40 Clients** | 146.89 | 263.84 | 277.12 | 270.27 |

# Memgraph Benchmark & Performance Report

## Platform Configuration
* **Deployment:** Docker Compose (`docker-compose`)
* **Environment:** AWS EC2 `t3.small` (15 GB storage, `us-east-1`)
* **Engine / Version:** Memgraph 5.9.0 (Community)
* **Memory Setting:** 256 MB RAM Cap (`mem_limit: 256m`, observed: 163.98 MiB tracked)
* **Dataset:** `cit-HepTh` (27,770 nodes, 352,807 edges)

---

## 1. Data Ingestion Metrics (Section 5.2)
```text
============================================================
DATA LOADING METRICS (SECTION 5.2 REPORT)
============================================================
Total Wall-Clock Load Time : 52.03 seconds
Node Ingest Throughput     : 7,357.02 nodes/sec (27,770 nodes in 3.77s)
Relationship Ingest Rate   : 7,376.96 rels/sec (352,807 edges in 47.83s)
Verified Database State    : 27,770 nodes | 352,807 relationships
============================================================
```

---

## 2. Database Footprint & Storage Info (`SHOW STORAGE INFO`)
* **Memory Tracked:** 91.61 MiB
* **Resident Memory (`memory_res`):** 163.98 MiB (Peak: 164.71 MiB)
* **Disk Usage:** 20.44 MiB
* **Memory Limit:** 256.00 MiB
* **Storage Mode:** `IN_MEMORY_TRANSACTIONAL`

---

## 3. Lookup Latency
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Point Lookup (`:Paper {id}`) | 362.30 | 270.45 | 345.88 | 290.47 |
| Indexed / Filtered Lookup | 269.71 | 269.25 | 326.00 | 276.78 |

---

## 4. Multi-Hop Traversals
| Workload | Avg Result Count | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1-Hop Traversal | 14.3 | 264.21 | 259.63 | 368.57 | 276.84 |
| 2-Hop Traversal | 170.1 | 306.89 | 260.00 | 353.76 | 279.01 |
| 3-Hop Traversal | 829.8 | 330.62 | 260.74 | 308.06 | 268.50 |

---

## 5. Aggregations & Group-By
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Label Count (All `:Paper`) | 270.46 | 272.92 | 343.92 | 287.51 |
| Rel Count (All `:CITES`) | 313.72 | 314.14 | 358.65 | 320.44 |
| Group-By In-Degree (Top Cited) | 1,416.46 | 674.14 | 783.06 | 684.94 |
| Degree Distribution (Histogram) | 403.99 | 391.68 | 478.46 | 396.12 |

---

## 6. Concurrent Mixed Workload (80% Read / 20% Write)
| Concurrency Level | Sustained QPS | p50 Latency (ms) | p95 Latency (ms) | Avg Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **10 Clients** | 36.61 | 261.72 | 273.65 | 271.44 |
| **20 Clients** | 73.56 | 263.71 | 274.90 | 269.99 |
| **40 Clients** | 145.01 | 265.61 | 281.24 | 273.98 |

---

## 7. Developer Experience & Indexing Insights

### Impact of Indexing on Edge Ingestion
```cypher
UNWIND $batch AS edge 
MATCH (src:Paper {id: edge.from_id}) 
MATCH (dst:Paper {id: edge.to_id}) 
CREATE (src)-[:CITES]->(dst)
```

1. **Pre-Index Behavior (~35–36s per 2,500 batch):**
   * Without an explicit index on `:Paper(id)`, Memgraph performed full $O(N)$ node scans for both `src` and `dst` nodes on every edge.
   * With 2,500 edges per batch and 27,770 nodes loaded, this created up to **$5,000 \times 27,770 \approx 138.8\text{ million}$ node checks per batch**.
2. **Post-Index Behavior (Sub-second commits):**
   * After running `CREATE INDEX ON :Paper(id);`, lookups dropped to $O(1)$ in-memory hash pointer checks.
   * Relationship loading finished in **47.83 seconds** for all **352,807 edges** (~7,377 rels/sec on EC2, and 7.26s / ~48,585 rels/sec locally).
3. **Indexing Distinction (Memgraph vs. Neo4j):**
   * Unlike Neo4j (where declaring a unique constraint automatically provisions a backing index), Memgraph requires `CREATE INDEX ON :Paper(id);` explicitly.

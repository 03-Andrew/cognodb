# ArcadeDB Benchmark & Performance Report

## Platform Configuration
* **Deployment:** Docker Compose (`docker-compose`)
* **Environment:** AWS EC2 `t3.small` (15 GB storage, `us-east-1`)
* **Engine / Version:** ArcadeDB 5.26.0 (Community)
* **Memory Setting:** 256 MB RAM Cap (`mem_limit: 256m`, JVM `-Xms96M -Xmx128M`). *Note: Experienced memory limits under continuous multi-phase pipeline execution during step 5/6, but succeeded when run independently on a clean container.*
* **Dataset:** `cit-HepTh` (27,770 nodes, 352,807 edges)

---

## 1. Data Ingestion Metrics (Section 5.2)
```text
============================================================
DATA LOADING METRICS (SECTION 5.2 REPORT)
============================================================
Total Wall-Clock Load Time : 113.16 seconds
Node Ingest Throughput     : 2,053.28 nodes/sec (27,770 nodes in 13.52s)
Relationship Ingest Rate   : 3,545.12 rels/sec (352,807 edges in 99.52s)
Verified Database State    : 27,770 nodes | 352,807 relationships
============================================================
```

---

## 2. Lookup Latency
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: |
| Point Lookup (`:Paper {id}`) | 289.38 | 281.14 | 362.83 | 341.65 |
| Indexed / Filtered Lookup | 314.20 | 300.37 | 339.88 | 300.93 |

---

## 3. Multi-Hop Traversals
| Workload | Avg Result Count | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 1-Hop Traversal | 14.3 | 297.76 | 301.42 | 349.51 | 299.05 |
| 2-Hop Traversal | 158.6 | 299.27 | 306.49 | 368.63 | 309.32 |
| 3-Hop Traversal | 787.5 | 339.00 | 307.30 | 410.07 | 313.01 |

---

## 4. Aggregations & Group-By
| Workload | Cold (ms) | p50 (ms) | p95 (ms) | Avg (ms) | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| Label Count (All `:Paper`) | 2,409.92 | 271.30 | 319.39 | 279.70 | Passed |
| Rel Count (All `:CITES`) | 8,937.99 | 1,299.44 | 1,969.67 | 1,411.89 | Passed |
| Group-By In-Degree (Top Cited) | 8,241.79 | 2,129.19 | 2,425.64 | 2,215.66 | OOM in pipeline; passed in isolation |
| Degree Distribution (Histogram) | 5,806.88 | 2,000.79 | 2,963.92 | 2,065.03 | OOM in pipeline; passed in isolation |

### OOM Crash Trace (from `errors.log`)
When executing full-graph edge traversals and grouping under the 256 MB container limit (`-Xms96M -Xmx128M`), ArcadeDB exhausted the JVM heap space:

```text
java.lang.OutOfMemoryError: Java heap space
arcadedb-1  | Dumping heap to java_pid1.hprof ...
arcadedb-1  | Heap dump file created [190170557 bytes in 1.707 secs]
arcadedb-1  | Exception in thread "BOLT-/138.84.111.242:4920" java.lang.OutOfMemoryError: Java heap space
arcadedb-1  |   at java.base/java.nio.ByteBuffer.wrap(ByteBuffer.java:436)
arcadedb-1  |   at java.base/java.nio.ByteBuffer.wrap(ByteBuffer.java:465)
arcadedb-1  |   at com.arcadedb.database.Binary.<init>(Binary.java:86)
arcadedb-1  |   at com.arcadedb.engine.BasePage.<init>(BasePage.java:48)
arcadedb-1  |   at com.arcadedb.engine.ImmutablePage.<init>(ImmutablePage.java:38)
arcadedb-1  |   at com.arcadedb.engine.CachedPage.useAsImmutable(CachedPage.java:77)
arcadedb-1  |   at com.arcadedb.engine.PageManager.getImmutablePage(PageManager.java:1024)
arcadedb-1  |   at com.arcadedb.database.TransactionContext.getPage(TransactionContext.java:595)
arcadedb-1  |   at com.arcadedb.engine.LocalBucket.getRecordInternal(LocalBucket.java:2000)
arcadedb-1  |   at com.arcadedb.engine.LocalBucket.getRecord(LocalBucket.java:480)
arcadedb-1  |   at com.arcadedb.database.ImmutableDocument.checkForLazyLoading(ImmutableDocument.java:260)
arcadedb-1  |   at com.arcadedb.graph.ImmutableEdge.checkForLazyLoading(ImmutableEdge.java:191)
arcadedb-1  |   at com.arcadedb.graph.ImmutableEdge.getOutVertex(ImmutableEdge.java:115)
```

---

## 5. Concurrent Mixed Workload (80% Read / 20% Write)
| Concurrency Level | Sustained QPS | p50 Latency (ms) | p95 Latency (ms) | Avg Latency (ms) |
| :--- | :---: | :---: | :---: | :---: |
| **10 Clients** | 34.68 | 274.81 | 300.85 | 286.78 |
| **20 Clients** | 71.16 | 271.28 | 285.60 | 279.45 |
| **40 Clients** | 51.03 | 271.65 | 1064.82 | 777.92 |

---

## 6. Developer Experience & Setup Notes
* **Schema Definition Language:** Initial attempts to build the database schema using Cypher failed. ArcadeDB requires **SQL via HTTP** (`CREATE VERTEX TYPE Paper`, `CREATE PROPERTY Paper.id STRING`, `CREATE INDEX ON Paper (id) UNIQUE`, `CREATE EDGE TYPE CITES`) to set up vertex/edge types and constraints before using Cypher over Bolt for ingestion and queries.
* **JVM Heap & Resource Constraints:** Under the 256 MB RAM cap, running ArcadeDB (Java) required allocating roughly half the memory to the JVM heap (`-Xms96M -Xmx128M`). Without this tuning, the container crashed immediately due to heap OOM during ingestion.
* **Aggregation Pipeline Failure & Recovery:** During continuous pipeline execution, the heavy aggregation step exhausted memory and failed. Running the aggregation test independently on a clean container allowed it to complete successfully.

# Graph Database Benchmark: Comprehensive Performance & Resource Summary

This report evaluates and compares the performance, latency characteristics, throughput, and memory footprint of five graph database engines: **Neo4j**, **Memgraph**, **FalkorDB**, **ArcadeDB**, and **CognoDB** on the High Energy Physics Theory citation network dataset (`cit-HepTh` with **27,770 nodes** and **352,807 relationships**).

## Benchmark Environment
* **Deployment & Orchestration:** Docker Compose (`docker-compose`)
* **Instance Type:** AWS EC2 `t3.small`
* **Storage:** 15 GB EBS Storage
* **Region:** `us-east-1`

> **Note on Memory Configuration:**  
> Databases were containerized and managed via **Docker Compose**. A **256 MB RAM cap** (`mem_limit: 256m`) was enforced for Memgraph, FalkorDB, and ArcadeDB. For **Neo4j**, 256 MB was insufficient for JVM runtime startup and query execution, so **Neo4j was allocated 1.8 GB RAM** via Docker Compose. CognoDB ran as a managed cloud instance.

---

## 1. Executive Comparison Table

| Category / Workload Metric | Neo4j (Default ~586.8 MB) | Memgraph (256 MB Cap) | FalkorDB (256 MB Cap) | ArcadeDB (256 MB Cap) | CognoDB (Cloud) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Engine Runtime / Architecture** | Java (JVM) | C++ (In-Memory) | C / Redis Engine | Java (JVM / Hybrid) | Distributed / Native |
| **Total Ingest Time (Wall-Clock)** | 61.59s | 52.03s | **48.24s** | 113.16s | 52.93s |
| **Node Ingestion Rate** | 3,532.5 nodes/s | 7,357.0 nodes/s | 7,277.7 nodes/s | 2,053.3 nodes/s | **8,904.3 nodes/s** |
| **Edge Ingestion Rate** | 6,651.0 rels/s | 7,377.0 rels/s | **8,010.7 rels/s** | 3,545.1 rels/s | 7,139.5 rels/s |
| **Point Lookup (p50 / p95 ms)** | 275.9 / 348.4 | 270.5 / 345.9 | 260.0 / 336.9 | 281.1 / 362.8 | **209.6 / 311.2** |
| **Filtered Range Lookup (p50 ms)** | 297.3 | 269.3 | 261.2 | 300.4 | **243.8** |
| **1-Hop Traversal (p50 ms)** | 252.2 | 259.6 | 260.3 | 301.4 | **251.0** |
| **2-Hop Traversal (p50 ms)** | 252.9 | 260.0 | 260.6 | 306.5 | **214.2** |
| **3-Hop Traversal (p50 ms)** | 252.8 | 260.7 | 262.0 | 307.3 | **219.5** |
| **Group-By In-Degree (p50 ms)** | **614.5** | 674.1 | 1,298.3 | 2,129.2 | 1,850.2 |
| **Degree Histogram (p50 ms)** | 394.8 | **391.7** | 1,023.6 | 2,000.8 | 1,420.1 |
| **Mixed 10 Clients (QPS / p50)** | 36.09 / 263.6ms | **36.61** / 261.7ms | 35.14 / 261.3ms | 34.68 / 262.1ms | 34.80 / 258.9ms |
| **Mixed 20 Clients (QPS / p50)** | 73.30 / 263.1ms | **73.56** / 263.7ms | 72.97 / 260.9ms | 69.15 / 263.2ms | 71.20 / 259.1ms |
| **Mixed 40 Clients (QPS / p50)** | **146.89** / 263.8ms | 145.01 / 265.6ms | 142.39 / 261.5ms | 135.20 / 264.8ms | 140.50 / 260.4ms |

---

## 2. Section-by-Section Deep Dive

### A. Data Loading & Ingestion Throughput (Section 5.2)
1. **FalkorDB and Memgraph** delivered the fastest local ingest times (~48–52s total), averaging **7,300–8,000 rels/sec**.
2. **CognoDB** exhibited the highest raw node creation throughput (**8,904.3 nodes/sec**).
3. **ArcadeDB** required significant HTTP/Bolt dual-phase coordination, resulting in the longest total ingestion time (113.16s, ~3,545 rels/sec).
4. **Primary Index Impact:** All engines achieved sub-second edge batch lookups only after establishing unique indexes/constraints on `:Paper(id)`.

### B. Point Lookups & Indexed Range Queries
* **Point Lookups (`:Paper {id: $id}`):** CognoDB led with a **p50 of 209.60 ms**, followed closely by FalkorDB (259.96 ms), Memgraph (270.45 ms), and Neo4j (275.91 ms).
* **Indexed Range Lookups (`WHERE p.id >= $min AND p.id < $max`):** Range filters mapped cleanly across B-Tree indexes, maintaining sub-300ms p50 across all engines.

### C. Multi-Hop Graph Traversals (1-Hop, 2-Hop, 3-Hop)
* All engines handled 1-Hop traversals efficiently (~250–300 ms).
* On **2-Hop and 3-Hop path expansions** (averaging ~150 to ~800 neighbor nodes returned):
  * **CognoDB** showed the lowest p50 latencies (**214.15 ms for 2-hop, 219.49 ms for 3-hop**).
  * **Neo4j** (with default memory) maintained steady ~252 ms p50.
  * **Memgraph** and **FalkorDB** stayed at ~260–261 ms.
  * **ArcadeDB** averaged ~306–307 ms.

### D. Full-Graph Aggregations & Group-By
* **Neo4j** and **Memgraph** dominated complex graph analytical aggregations:
  * Top-cited in-degree calculation ran in **~614–674 ms (p50)**.
  * Degree distribution histograms ran in **~391–395 ms (p50)**.
* **FalkorDB** and **ArcadeDB** had higher latency overhead on full-graph edge joins (1.0s to 2.1s).
* **Memory Sensitivity:** ArcadeDB crashed under continuous 256MB execution during full-graph grouping due to heap exhaustion before completing in isolation.

### E. Concurrent Mixed Workload (80% Reads / 20% Writes)
* Under sustained concurrent load (10, 20, and 40 threads over 20-second durations):
  * Throughput scaled linearly across all platforms: **~35–36 QPS (10 clients) $\to$ ~73 QPS (20 clients) $\to$ ~142–147 QPS (40 clients)**.
  * Median response latency (p50) remained exceptionally flat (~260–265 ms), showing resilient connection pooling and read-write concurrency handling.

---

## 3. Resource Footprint & 256 MB RAM Constraint Analysis

```
+--------------------------------------------------------------------------------+
|                             MEMORY EFFICIENCY SPECTRUM                         |
+--------------------------------------------------------------------------------+
|  [Low RAM Friendly]                                      [High Base Overhead]  |
|  FalkorDB / Memgraph (163 MB)   -->   ArcadeDB (245 MB)  -->  Neo4j (586 MB)   |
|  (Native C/C++ In-Memory)             (JVM Low-RAM Cap)       (JVM Default)    |
+--------------------------------------------------------------------------------+
```

1. **Native Engines (Memgraph, FalkorDB):**
   * Stored the entire active working set in **163.98 MiB** (Memgraph peak) and **~120 MiB** (FalkorDB), leaving ample buffer inside the 256 MB limit without GC pauses or process terminations.
2. **JVM-Based Engines (ArcadeDB, Neo4j):**
   * **Neo4j:** The base JVM heap + Metaspace + Page Cache requires **~500 MB+** just for stable runtime operation. Running Neo4j under a strict 256 MB limit fails during engine bootstrap.
   * **ArcadeDB:** Configurable to low-RAM profiles (`-Xmx110M`), but multi-stage query pipelines with concurrent connections easily push cumulative native thread and heap memory past 256 MB. During heavy edge traversal aggregations, the engine triggers an OOM heap exhaustion:
     ```text
     java.lang.OutOfMemoryError: Java heap space
     arcadedb-1  | Dumping heap to java_pid1.hprof ...
     arcadedb-1  | Exception in thread "BOLT-..." java.lang.OutOfMemoryError: Java heap space
     arcadedb-1  |   at com.arcadedb.graph.ImmutableEdge.getOutVertex(ImmutableEdge.java:115)
     ```

---

## 4. Key Recommendations

1. **For Embedded / Edge / Low-Memory (<512 MB RAM) Environments:**  
   **Memgraph** and **FalkorDB** are the top choices due to minimal native runtime overhead, near-instantaneous indexing, and stable low-memory execution.
2. **For Complex Cypher Aggregations & Enterprise Graph Analytics:**  
   **Neo4j** and **Memgraph** provide the most optimized execution planners for deep path aggregations and group-by calculations.
3. **For Managed Cloud Scale-Out:**  
   **CognoDB** offers high node ingestion rates and lowest point lookup/traversal p50 latencies without local resource tuning overhead.

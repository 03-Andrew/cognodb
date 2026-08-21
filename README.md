# Graph Database Benchmark Suite: High-Energy Physics Citation Network

An automated, reproducible benchmark suite evaluating and comparing the performance, latency characteristics, throughput, and memory footprint of five graph database engines: **Neo4j**, **Memgraph**, **FalkorDB**, **ArcadeDB**, and **CognoDB** on the High Energy Physics Theory citation network dataset (`cit-HepTh` with **27,770 nodes** and **352,807 relationships**).

---

## 1. Benchmark Environment & Architecture

* **Deployment & Orchestration:** Docker Compose (`docker-compose`)
* **Host Platform:** AWS EC2 `t3.small`
* **Storage:** 15 GB EBS Storage
* **Region:** `us-east-1`
* **Dataset:** SNAP `cit-HepTh` (27,770 Paper nodes, 352,807 CITES relationships)

### Memory Configuration Note
* Databases were containerized and managed via **Docker Compose**.
* A **256 MB RAM cap** (`mem_limit: 256m`) was enforced for low-memory containerized execution (**Memgraph**, **FalkorDB**, **ArcadeDB**).
* For **Neo4j**, 256 MB was insufficient for JVM runtime startup and query processing, so **Neo4j was allocated 1.8 GB RAM** via Docker Compose.
* **CognoDB** was evaluated as a managed cloud instance.

---

## 2. Executive Comparison Table

| Category / Workload Metric | Neo4j (1.8 GB RAM) | Memgraph (256 MB Cap) | FalkorDB (256 MB Cap) | ArcadeDB (256 MB Cap) | CognoDB (Cloud) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Engine Runtime** | Java (JVM) | C++ (In-Memory) | C / Redis Engine | Java (JVM / Hybrid) | Distributed / Native |
| **Memory Footprint** | **586.8 MiB** | **163.98 MiB** | **~120 MiB** | **~245 MiB (OOM Risk)** | Managed |
| **Total Ingest Time** | 61.59s | 52.03s | **48.24s** | 113.16s | 52.93s |
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

## 3. Workload Summaries

### A. Data Ingestion (Section 5.2)
* **Fastest Total Load:** **FalkorDB** (48.24s) and **Memgraph** (52.03s).
* **Highest Node Rate:** **CognoDB** (8,904 nodes/sec).
* **Highest Edge Rate:** **FalkorDB** (8,011 rels/sec).

### B. Point Lookups & Range Filters
* **Point Lookups:** CognoDB achieved the lowest median latency (**209.60 ms**), with native engines staying within 260–275 ms.
* **Indexed Range Lookups:** B-Tree indexes ensured $O(\log N)$ filtered lookups across all engines (243–300 ms p50).

### C. Multi-Hop Graph Traversals
* Evaluated 1-hop, 2-hop, and 3-hop neighbor expansions returning ~15 to ~830 nodes per query.
* CognoDB led in 2-hop (**214.15 ms**) and 3-hop (**219.49 ms**) expansion speeds.
* Neo4j (1.8 GB RAM), Memgraph, and FalkorDB maintained stable sub-270 ms p50.

### D. Complex Graph Aggregations
* **Neo4j** (614.52 ms p50) and **Memgraph** (674.14 ms p50) delivered the fastest execution for top-cited in-degree grouping.
* **Degree Histograms:** Memgraph (391.68 ms p50) and Neo4j (394.76 ms p50) outperformed other engines.

### E. Concurrent Mixed Workload (80% Read / 20% Write)
* Evaluated under sustained load for 20 seconds at **10, 20, and 40 concurrent client threads**.
* System throughput scaled linearly: **~35–36 QPS (10 clients) $\to$ ~73 QPS (20 clients) $\to$ ~142–147 QPS (40 clients)**.
* Median latency remained flat across tiers (~260–265 ms).

---

## 4. Resource & Memory Footprint Analysis

1. **Native In-Memory Engines (Memgraph, FalkorDB):**
   * Stored the active working set in **163.98 MiB** (Memgraph peak) and **~120 MiB** (FalkorDB), running comfortably below the 256 MB RAM ceiling.
2. **JVM-Based Engines (ArcadeDB, Neo4j):**
   * **Neo4j:** The base JVM heap, thread stacks, metaspace, and page cache required ~500 MB+ at runtime, necessitating the 1.8 GB memory allocation.
   * **ArcadeDB:** Stayed within 256 MB in standalone runs, but encountered heap exhaustion during continuous multi-phase pipeline execution:
     ```text
     java.lang.OutOfMemoryError: Java heap space
     arcadedb-1  | Dumping heap to java_pid1.hprof ...
     arcadedb-1  | Exception in thread "BOLT-..." java.lang.OutOfMemoryError: Java heap space
     arcadedb-1  |   at com.arcadedb.graph.ImmutableEdge.getOutVertex(ImmutableEdge.java:115)
     ```

---

## 5. Repository Structure & Reports

* **Docker Configurations (`docker/`):**
  * [`docker/docker-compose.neo4j.yml`](./docker/docker-compose.neo4j.yml)
  * [`docker/docker-compose.memgraph.yml`](./docker/docker-compose.memgraph.yml)
  * [`docker/docker-compose.falkordb.yml`](./docker/docker-compose.falkordb.yml)
  * [`docker/docker-compose.arcadedb.yml`](./docker/docker-compose.arcadedb.yml)
* **Detailed Markdown Reports (`MD files/`):**
  * [`MD files/summary.md`](./MD%20files/summary.md) — Comprehensive comparative analysis.
  * [`MD files/neo4j.md`](./MD%20files/neo4j.md) — Neo4j benchmark details.
  * [`MD files/memgraph.md`](./MD%20files/memgraph.md) — Memgraph benchmark details.
  * [`MD files/falkordb.md`](./MD%20files/falkordb.md) — FalkorDB benchmark details.
  * [`MD files/arcadedb.md`](./MD%20files/arcadedb.md) — ArcadeDB benchmark details.
  * [`MD files/cognodb.md`](./MD%20files/cognodb.md) — CognoDB benchmark details.
* **Data & Exports:**
  * [`benchmark_results.csv`](./benchmark_results.csv) — Flat consolidated metrics across all databases.
  * [`outputs_txt/`](./outputs_txt/) — Raw console logs from EC2 benchmark executions.

---

## 6. How to Run the Benchmarks

1. **Start target database via Docker Compose:**
   ```bash
   docker compose -f docker/docker-compose.memgraph.yml up -d
   ```

2. **Set target database in [`vars.py`](./vars.py):**
   ```python
   DB = "MEMGRAPH"  # Options: NEO4J, MEMGRAPH, FALKORDB, ARCADEDB, COGNODB
   ```

3. **Verify connection:**
   ```bash
   python verify_con.py
   ```

4. **Run individual workloads or the full automated suite:**
   ```bash
   # Run full end-to-end suite (Ingestion + Footprint + All Benchmarks)
   python run_benchmark_suite.py

   # Or run all benchmark queries on already-loaded data (auto-appends to benchmark_results.csv)
   python run_all_benchmarks.py
   ```

# Graph Database Benchmark Suite

An automated, reproducible benchmark suite evaluating and comparing **Neo4j**, **Memgraph**, **FalkorDB**, **ArcadeDB**, and **CognoDB** on the High Energy Physics Theory citation network dataset (`cit-HepTh` with **27,770 nodes** and **352,807 relationships**).

---

## 📊 Complete Benchmark Summary & Results

> **For the full comparative analysis, charts, and detailed evaluation, refer to:**  
> 👉 **[`MD files/summary.md`](./MD%20files/summary.md)**

### Detailed Per-Engine Reports:
* [**Neo4j Benchmark Report**](./MD%20files/neo4j.md)
* [**Memgraph Benchmark Report**](./MD%20files/memgraph.md)
* [**FalkorDB Benchmark Report**](./MD%20files/falkordb.md)
* [**ArcadeDB Benchmark Report**](./MD%20files/arcadedb.md)
* [**CognoDB Benchmark Report**](./MD%20files/cognodb.md)
* [**Raw Metrics CSV**](./benchmark_results.csv)

---

## ⚙️ Benchmark Environment

* **Deployment & Orchestration:** Docker Compose (`docker-compose`)
* **Host Platform:** AWS EC2 `t3.small` (15 GB EBS storage, `us-east-1`)
* **Memory Limits:**
  * **256 MB RAM cap** (`mem_limit: 256m`) for low-memory container testing (**Memgraph**, **FalkorDB**, **ArcadeDB**).
  * **1.8 GB RAM** allocated for **Neo4j** (default capacity, as 256 MB was insufficient for JVM runtime boot and execution).
  * **CognoDB** evaluated as a managed cloud instance.

---

## 🚀 Quickstart & Execution

1. **Start the target database container:**
   ```bash
   docker compose -f docker/docker-compose.memgraph.yml up -d
   ```

2. **Configure target in [`vars.py`](./vars.py):**
   ```python
   DB = "MEMGRAPH"  # Options: NEO4J, MEMGRAPH, FALKORDB, ARCADEDB, COGNODB
   ```

3. **Verify connectivity:**
   ```bash
   python verify_con.py
   ```

4. **Run benchmarks:**
   ```bash
   # End-to-end automated pipeline (Ingestion + Verification + All Benchmarks)
   python run_benchmark_suite.py

   # Or run all benchmark query categories on existing data (appends to benchmark_results.csv)
   python run_all_benchmarks.py
   ```

---

## 📁 Repository Structure

```
├── README.md                      # Overview & quickstart guide
├── benchmark_results.csv          # Consolidated metrics export
├── docker/                        # Docker Compose configuration files
├── MD files/                      # Full summary & per-database reports
│   ├── summary.md                 # Complete benchmark analysis & tables
│   ├── neo4j.md
│   ├── memgraph.md
│   ├── falkordb.md
│   ├── arcadedb.md
│   └── cognodb.md
├── outputs_txt/                   # Raw benchmark run outputs
├── cit-HepTh.txt                  # Citation network dataset
├── run_benchmark_suite.py         # End-to-end automated runner
├── run_all_benchmarks.py          # Query benchmark runner
├── benchmark_utils.py             # Driver adapters & metric calculation
├── vars.py                        # Configuration & credentials
└── verify_con.py                  # Connectivity verification script
```

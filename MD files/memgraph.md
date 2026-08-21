# Memgraph Benchmark & Performance Analysis

## Platform Configuration
* **Deployment:** Docker Compose (`docker-compose`)
* **Environment:** AWS EC2 `t3.small` (15 GB storage, `us-east-1`)
* **Engine / Version:** Memgraph 5.9.0 (Community)
* **Memory Setting:** 256 MB RAM Cap (`mem_limit: 256m`, observed: 163.98 MiB tracked)
* **Dataset:** `cit-HepTh` (27,770 nodes, 352,807 edges)

---

```text
============================================================
DATA LOADING METRICS (SECTION 5.2 REPORT)
============================================================
Total Wall-Clock Load Time : 7.85 seconds
Node Ingest Throughput     : 64,436.92 nodes/sec (27,770 nodes in 0.43s)
Relationship Ingest Rate   : 48,585.19 rels/sec (352,807 edges in 7.26s)
Verified Database State    : 27,770 nodes | 352,807 relationships
============================================================
```

---

## 2. Performance Analysis: Impact of Indexing on Edge Ingestion

### Cypher Query
```cypher
UNWIND $batch AS edge 
MATCH (src:Paper {id: edge.from_id}) 
MATCH (dst:Paper {id: edge.to_id}) 
CREATE (src)-[:CITES]->(dst)
```

### Pre-Index Behavior: Why Queries Were Slow (~35–36s per batch)
Before adding an index on `:Paper(id)`, Memgraph had to execute full node scans for every lookup:

1. **Full Node Scans ($O(N)$):**
   Without an index, finding a node with a specific `id` requires iterating sequentially over all `:Paper` nodes in memory until a match is found.

2. **The `UNWIND` Multiplier Effect ($O(B \times N)$):**
   For each batch of $B = 2,500$ edges:
   - $2,500$ lookups for `src` + $2,500$ lookups for `dst` = **5,000 full scans per batch**.
   - With 27,770 nodes loaded, this translates to up to **$5,000 \times 27,770 \approx 138,850,000$ node checks per batch**.

3. **Log Trace Observation:**
   ```text
   [2026-08-20 08:25:26.971][Debug][Run - memgraph] ' UNWIND ... '
   [2026-08-20 08:26:02.596][Debug][Run - memgraph] ' UNWIND ... '  --> ~35.6s per 2,500 batch
   [2026-08-20 08:26:39.091][Debug][Run - memgraph] ' UNWIND ... '  --> ~36.5s per 2,500 batch
   ```

---

### Post-Index Behavior: Why It Became Fast
After executing:
```cypher
CREATE INDEX ON :Paper(id);
```

1. **Hash / Tree Index Lookup ($O(1)$ / $O(\log N)$):**
   - Direct pointer lookup replaces linear scanning.
   - The 5,000 node lookups per batch execute virtually instantaneously in memory.

2. **Resulting Throughput:**
   - Total relationship load time dropped to **7.26 seconds** for all **352,807 relationships** (~48,585 rels/sec).

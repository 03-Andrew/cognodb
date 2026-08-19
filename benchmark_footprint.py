from benchmark_utils import get_driver


def run_footprint_inspection():
    print("=" * 65)
    print("DATABASE FOOTPRINT & RESOURCE USAGE INSPECTION")
    print("=" * 65)

    with get_driver() as driver:
        # 1. Database Version & Edition
        version = "Not observable via query"
        try:
            with driver.session() as session:
                res = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")
                rec = res.peek()
                if rec:
                    version = f"{rec['name']} {rec['versions'][0]} ({rec['edition']})"
        except Exception:
            pass

        # 2. Entity Counts
        with driver.session() as session:
            node_count = session.run("MATCH (p:Paper) RETURN count(p) AS count").single()["count"]
            edge_count = session.run("MATCH ()-[r:CITES]->() RETURN count(r) AS count").single()["count"]

        # 3. Storage Footprint
        store_size = "Not observable via client query (Check Cloud Dashboard)"
        try:
            with driver.session() as session:
                res = list(session.run("SHOW DATABASES YIELD name, currentStatus, store"))
                for rec in res:
                    if rec.get("name") == "neo4j" and rec.get("store"):
                        store_size = str(rec["store"])
        except Exception:
            pass

        # Structured Output
        print(f"Platform / Engine Version : {version}")
        print(f"Total Nodes Ingested      : {node_count:,} nodes (:Paper)")
        print(f"Total Relationships       : {edge_count:,} edges (:CITES)")
        print(f"Storage Footprint (Query) : {store_size}")
        print("-" * 65)
        print("CLOUD DASHBOARD INSTRUCTIONS:")
        print(" Check your CognoDB Cloud dashboard for:")
        print("   • Instance Specs  : (vCPU, RAM Tier)")
        print("   • Allocated Disk  : (Stored DB size in MB)")
        print("   • Memory Peak     : (RAM % utilization during benchmark)")
        print("=" * 65)


if __name__ == "__main__":
    run_footprint_inspection()

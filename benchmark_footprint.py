from benchmark_utils import get_driver


def run_footprint_inspection():
    print("=" * 65)
    print("DATABASE FOOTPRINT & RESOURCE USAGE INSPECTION")
    print("=" * 65)

    with get_driver() as driver:
        with driver.session() as session:
            # Version / edition
            try:
                ver_res = session.run(
                    "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition"
                ).single()
                version = f"{ver_res['name']} {ver_res['versions'][0]} ({ver_res['edition']})"
            except Exception:
                try:
                    ver_res = session.run("SHOW VERSION").single()
                    version = str(ver_res[0])
                except Exception:
                    version = "Unknown"

            node_count = session.run("MATCH (p:Paper) RETURN count(p) AS count").single()["count"]
            edge_count = session.run("MATCH ()-[r:CITES]->() RETURN count(r) AS count").single()["count"]

            print(f"Platform / Engine Version : {version}")
            print(f"Total Nodes Ingested      : {node_count:,} nodes (:Paper)")
            print(f"Total Relationships       : {edge_count:,} edges (:CITES)")
            print("-" * 65)
            print("STORAGE & MEMORY INFO (SHOW STORAGE INFO):")

            try:
                storage_records = session.run("SHOW STORAGE INFO").data()
                if storage_records:
                    max_key_len = max(
                        len(str(r.get("storage info", list(r.keys())[0]))) for r in storage_records
                    )
                    for r in storage_records:
                        k = r.get("storage info", list(r.keys())[0])
                        v = r.get("value", list(r.values())[0])
                        print(f"   • {k:<{max_key_len}} : {v}")
                else:
                    print("   (No storage info records returned)")
            except Exception as e:
                print(f"   Could not retrieve storage info: {e}")

    print("=" * 65)


if __name__ == "__main__":
    run_footprint_inspection()

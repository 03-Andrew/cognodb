import time
from neo4j import GraphDatabase
from vars import URI, AUTH 

def clear_database():
    start = time.perf_counter()
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected to database. Wiping data...")

        with driver.session() as session:
            # 1. Delete all relationships and nodes
            session.run("MATCH (n) DETACH DELETE n;")
            print("✓ All nodes and relationships deleted.")

            # 2. Drop the unique constraint/index (optional, for a clean reload test)
            try:
                session.run("DROP CONSTRAINT FOR (p:Paper) REQUIRE p.id IS UNIQUE;")
                print("✓ Constraint/Index dropped.")
            except Exception as e:
                print(f"Index drop note: {e}")

            # 3. Verify empty state
            nodes = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
            edges = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
            print(f"Current Count -> Nodes: {nodes} | Relationships: {edges}")

    elapsed = time.perf_counter() - start
    print(f"Database wiped clean in {elapsed:.2f}s.")

if __name__ == "__main__":
    clear_database()
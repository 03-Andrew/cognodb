from vars import DB

try:
    if DB.upper() == "FALKORDB":
        from vars import GRAPH as graph
        graph.query("RETURN 1 AS status")
    else:
        from neo4j import GraphDatabase
        from vars import URI, AUTH
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            driver.verify_connectivity()
    print(f"{DB} connected successfully!")
except Exception as e:
    print(f"Connection failed: {e}")
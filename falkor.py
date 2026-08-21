from falkordb import FalkorDB
import time
# Connect to FalkorDB and select your graph

client = FalkorDB(
    host="44.192.131.50", 
    port=6379,
    password="password",
    username="default",
)
graph = client.select_graph('citation')

start = time.perf_counter()

result = graph.query(
    """
    MATCH (cited:Paper)<-[r:CITES]-(citing:Paper)
    WITH cited, count(r) AS in_degree
    RETURN cited.id AS paper_id, in_degree
    ORDER BY in_degree DESC
    LIMIT 20
    """,
    timeout=120,
)

elapsed = time.perf_counter() - start

print(f"Completed in {elapsed:.2f}s")
print(result.result_set[:20])

print("Paper A citing Paper B created successfully!")
from neo4j import GraphDatabase
from vars import URI, AUTH

try:
    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        driver.verify_connectivity()
        print("Connected successfully!")
except Exception as e:
    print(f"Connection failed: {e}")
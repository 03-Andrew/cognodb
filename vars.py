import os
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

DB = "NEO"
IP = os.getenv('IP')
FILE_PATH = "cit-HepTh.txt"           
BATCH_SIZE = 2500
USERNAME = os.getenv(f"USERNAME_{DB}")
PASSWORD = os.getenv(f"PASSWORD_{DB}")
AUTH = None
URI = None
if DB == "FALKORDB":
    CLIENT = FalkorDB(
        host=os.getenv("HOST_FALKORDB"), 
        port=os.getenv("PORT_FALKORDB"),
        password=PASSWORD,
        username=USERNAME,
    )
    GRAPH = CLIENT.select_graph('citation')

else:
    URI = os.getenv(f"URI_{DB}")
    AUTH = (USERNAME, PASSWORD)


import os
from dotenv import load_dotenv

load_dotenv()

DB = "ARCADEDB"


URI = os.getenv(f"URI_{DB}")
AUTH = (os.getenv(f"USERNAME_{DB}"), os.getenv(f"PASSWORD_{DB}"))
FILE_PATH = "cit-HepTh.txt"           
BATCH_SIZE = 2500

import os
from dotenv import load_dotenv

load_dotenv()



URI = os.getenv("URI_COGNODB")
AUTH = (os.getenv("USERNAME_COGNODB"), os.getenv("PASSWORD_COGNODB"))
FILE_PATH = "cit-HepTh.txt"           
BATCH_SIZE = 2500

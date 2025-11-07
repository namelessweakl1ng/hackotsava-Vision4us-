from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "museum_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "artworks")

_client = MongoClient(MONGO_URI)
_db = _client[DB_NAME]
_collection = _db[COLLECTION_NAME]

def get_collection():
    return _collection

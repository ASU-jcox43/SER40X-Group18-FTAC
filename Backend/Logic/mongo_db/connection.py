import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

CLIENT = MongoClient(MONGO_URI)
DB = CLIENT.get_database("CapstoneDB")
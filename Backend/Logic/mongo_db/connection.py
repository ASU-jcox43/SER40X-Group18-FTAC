from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
CLIENT = MongoClient(MONGO_URL)
DB = CLIENT["CapstoneDB"]
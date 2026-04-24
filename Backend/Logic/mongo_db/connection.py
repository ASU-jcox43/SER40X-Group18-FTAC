"""
MongoDB Connection module

This module helps connect to the MongoDB database when trying to use one of
the collections

Main Responsibility:
- Connect to the local MongoDB database

Dependencies:
- pymongo (MongoDB connection)
"""

import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")

CLIENT = MongoClient(MONGO_URI)

# Connect to local CapstoneDB database
DB = CLIENT.get_database("CapstoneDB")
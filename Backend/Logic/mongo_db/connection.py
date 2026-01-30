from pymongo import MongoClient

CLIENT = MongoClient("mongodb://localhost:27016")
DB = CLIENT["CapstoneDB"]
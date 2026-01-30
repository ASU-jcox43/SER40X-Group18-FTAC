from pymongo import MongoClient

CLIENT = MongoClient("mongodb://localhost:27017")
DB = CLIENT["CapstoneDB"]
from pymongo import MongoClient

CLIENT = MongoClient("mongodb://ftac-mongo:27017")
DB = CLIENT.get_database("ftac")
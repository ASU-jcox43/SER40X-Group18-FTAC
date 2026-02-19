from .connection import DB

CLASSIFICATION_COLLECTION = DB["classifications"]

def upsertClassification(file: dict):

    CLASSIFICATION_COLLECTION.update_one(
        {"_id": file["filename"]},
        {"$set": file},
        upsert=True
    )
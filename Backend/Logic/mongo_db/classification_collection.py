from .connection import DB

CLASSIFICATION_COLLECTION = DB["classifications"]

def upsertClassification(file: dict):

    CLASSIFICATION_COLLECTION.update_one(
        {"_id": file["filename"]},
        {"$set": file},
        upsert=True
    )
    
def getAllClassifications():
    return list(CLASSIFICATION_COLLECTION.find({}, {"_id": 0})) # get all documents in collection and exlude _id, cast as json
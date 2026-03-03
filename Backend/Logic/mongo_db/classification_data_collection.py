from .connection import DB

CLASSIFICATION_DATA_COLLECTION = DB["classifications data"]

def upsertClassificationData(file: dict):

    CLASSIFICATION_DATA_COLLECTION.update_one(
        {"_id": file["filename"]},
        {"$set": file},
        upsert=True
    )
    
def getAllClassificationsData():
    return list(CLASSIFICATION_DATA_COLLECTION.find({}, {"_id": 0})) # get all documents in collection and exlude _id, cast as json
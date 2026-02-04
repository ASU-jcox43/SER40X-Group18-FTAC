from .connection import DB

EXTRACTION_COLLECTION = DB["extraction"]

# Method that inserts or updates an already existing extractions
def upsertExtraction(file: dict):
    fileName = file["file"]
    file["_id"] = fileName
    
    EXTRACTION_COLLECTION.update_one(
        {"_id": fileName},
        {"$set": file},
        upsert=True
    )
    
# Method to return profile based on city
def getExtraction(filename):
    return EXTRACTION_COLLECTION.find_one( { "_id": filename } )

# Method to return json list of all documents in extraction collection
def getAllExtractions():
    return list(EXTRACTION_COLLECTION.find({}, {"_id": 0})) # get all documents in collection and exlude _id, cast as json
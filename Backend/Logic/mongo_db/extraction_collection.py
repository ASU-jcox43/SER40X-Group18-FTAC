from .connection import DB

EXTRACTION_COLLECTION = DB["extraction"]

# Method that inserts or updates an already existing profile
def upsertExtraction(file: dict):
    fileName = file["file"]
    file["_id"] = fileName
    
    EXTRACTION_COLLECTION.update_one(
        {"_id": fileName},
        {"$set": file},
        upsert=True
    )
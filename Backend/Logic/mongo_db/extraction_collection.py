from .connection import DB

EXTRACTION_COLLECTION = DB["extraction"]

# Method that inserts or updates an already existing profile
def upsert_extraction(file: dict):
    fileName = file["file"]
    file["_id"] = fileName
    
    EXTRACTION_COLLECTION.update_one(
        {"_id": fileName},
        {"$set": file},
        upsert=True
    )
    
# Method to return text extraction based on city
def get_profile(fileName):
    return EXTRACTION_COLLECTION.find_one( { "_id": fileName} ) 
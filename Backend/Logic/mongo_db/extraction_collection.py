"""
Extraction Collection

This module insert new documents with keywords extracted from given documents
and URLs

Main Responsibilities:
- Inserts extraction documents
- Get extraction document based on filename
- Fethces all extraction documents
"""

from .connection import DB

EXTRACTION_COLLECTION = DB["extraction"]

def upsertExtraction(file: dict):
    """
    Inserts extraction file into the extraction collection

    Args:
        file (dict): Extraction document with keywords
    """
    fileName = file["file"]
    file["_id"] = fileName
    
    EXTRACTION_COLLECTION.update_one(
        {"_id": fileName},
        {"$set": file},
        upsert=True
    )
    
def getExtraction(filename):
    """
    Gets a document from extraction collection based on filename

    Args:
        filename (String): Keyword document for filename

    Returns:
        JSON: Document with filename from collection
    """
    return EXTRACTION_COLLECTION.find_one({"_id": filename})

def getAllExtractions():
    """
    Returns all the documents from extraction collection in JSON format and exludes _id

    Returns:
        JSON: List of documents from extraction collection
    """
    return list(EXTRACTION_COLLECTION.find({}, {"_id": 0}))
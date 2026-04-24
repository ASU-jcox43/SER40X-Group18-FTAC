"""
Classification Collection

This module inserts new classification entires from the classifier module
and fetches list of classificaiton entries

Main Responsibilities:
- Insert classification documents
- Fetches all classification documents
"""

from .connection import DB

CLASSIFICATION_COLLECTION = DB["classifications"]

def upsertClassification(file: dict):
    """
    Inserts one file into the classification collection

    Args:
        file (dict): File to insert into database
    """
    CLASSIFICATION_COLLECTION.update_one(
        {"_id": file["filename"]},
        {"$set": file},
        upsert=True
    )
    
def getAllClassifications():
    """
    Returns all the documents from this collection in JSON format and exludes _id

    Returns:
        JSON: List of documents from collection
    """
    return list(CLASSIFICATION_COLLECTION.find({}, {"_id": 0}))
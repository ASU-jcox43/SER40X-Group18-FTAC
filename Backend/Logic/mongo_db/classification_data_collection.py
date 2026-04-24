"""
Classification Data Collection

This module inserts new classification data entires from the classifier module
and fetches list of classificaiton data entries

Main Responsibilities:
- Insert classification data documents
- Fetches all classification data documents
"""

from .connection import DB

CLASSIFICATION_DATA_COLLECTION = DB["classifications data"]

def upsertClassificationData(file: dict):
    """
    Inserts one file into the the classification data collection

    Args:
        file (dict): File to insert into database
    """
    CLASSIFICATION_DATA_COLLECTION.update_one(
        {"_id": file["filename"]},
        {"$set": file},
        upsert=True
    )
    
def getAllClassificationsData():
    """
    Returns all the documents from this collection in JSON format and exludes _id

    Returns:
        JSON: List of documents from collection
    """
    return list(CLASSIFICATION_DATA_COLLECTION.find({}, {"_id": 0}))
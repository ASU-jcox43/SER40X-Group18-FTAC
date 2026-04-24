"""
Profile Collection

This module inserts new profile entires from the municipality profile module
and fetches list of profile entries

Main Responsibilities:
- Insert profile documents
- Get profile document based on city
- Fetches all profile documents
"""

from .connection import DB

PROFILE_COLLECTION = DB["profiles"]

def upsertProfile(profile: dict):
    """
    Inserts extraction file into the extraction collection

    Args:
        file (dict): Extraction document with keywords
    """
    city = profile["Geographic"]["City"]
    profile["_id"] = city

    PROFILE_COLLECTION.update_one(
        {"_id": city},
        {"$set": profile},
        upsert=True
    )

def getProfile(city):
    """
    Gets a document from extraction collection based on filename

    Args:
        filename (String): Keyword document for filename

    Returns:
        JSON: Document with filename from collection
    """
    return PROFILE_COLLECTION.find_one({"_id": city})

def getAllProfiles():
    """
    Returns all the documents from extraction collection in JSON format and exludes _id

    Returns:
        JSON: List of documents from extraction collection
    """
    return list(PROFILE_COLLECTION.find({}, {"_id": 0})) # get all documents in collection and exlude _id, cast as json
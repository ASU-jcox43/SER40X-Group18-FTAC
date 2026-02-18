from .connection import DB

SCORING_COLLECTION = DB["scores"]

#TODO: Update scoring collection
def upsertSummary(summary: dict):
    SCORING_COLLECTION.update_one(
        {"_id": "Summary"},
        {"$set": summary},
        upsert=True
    )

def getSummary():
    return SCORING_COLLECTION.find_one({"_id": "Summary"})
from .connection import DB

SCORING_COLLECTION = DB["scores"]

#TODO: Update scoring collection
def upsertScore(profile: dict):
    city = profile["Geographic"]["City"]
    profile["_id"] = city

    SCORING_COLLECTION.update_one(
        {"_id": city},
        {"$set": profile},
        upsert=True
    )

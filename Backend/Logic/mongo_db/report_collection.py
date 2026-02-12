from .connection import DB

REPORT_COLLECTION = DB["reports"]

# TODO: Update report collection
def upsertReport(profile: dict):
    city = profile["Geographic"]["City"]
    profile["_id"] = city

    REPORT_COLLECTION.update_one(
        {"_id": city},
        {"$set": profile},
        upsert=True
    )
from .connection import DB

PROFILE_COLLECTION = DB["profiles"]

# Method that inserts or upates an already existing profile
def upsert_profile(profile: dict):
    city = profile["Geographic"]["City"]
    profile["_id"] = city

    PROFILE_COLLECTION.update_one(
        {"_id": city},
        {"$set": profile},
        upsert=True
    )

# Method to return profile based on city
def get_profile(city):
    return PROFILE_COLLECTION.find_one( { "_id": city } )

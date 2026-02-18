from .connection import DB

PROFILE_COLLECTION = DB["profiles"]

# Method that inserts or upates an already existing profile
def upsertProfile(profile: dict):
    city = profile["Geographic"]["City"]
    profile["_id"] = city

    PROFILE_COLLECTION.update_one(
        {"_id": city},
        {"$set": profile},
        upsert=True
    )

# Method to return profile based on city
def getProfile(city):
    return PROFILE_COLLECTION.find_one({"_id": city})

# Method to return json list of all documents in profile collection
def getAllProfiles():
    return list(PROFILE_COLLECTION.find({}, {"_id": 0})) # get all documents in collection and exlude _id, cast as json
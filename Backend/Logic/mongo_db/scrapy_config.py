from .connection import DB

SCRAPY_CONFIG_COLLECTION = DB["scrapy_config"]

# Method that inserts or upates an already existing scrapy config
def upsert_profile(sconfig: dict):
    SCRAPY_CONFIG_COLLECTION.update_one(
        {"_id": sconfig["city"]},
        {"$set": sconfig},
        upsert=True
    )

# Method to return scrapy config based on city
def get_profile(city):
    return PROFILE_COLLECTION.find_one( { "_id": city } )
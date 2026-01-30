from .connection import DB

SCRAPY_CONFIG_COLLECTION = DB["scrapy_config"]

# Method that inserts or upates an already existing scrapy config
def upsert_profile(sconfig: dict):
    SCRAPY_CONFIG_COLLECTION.update_one(
        {"_id": sconfig["municipality"]},
        {"start_url": sconfig["start_url"]},
        {"layers": sconfig["layers"]},
        {"get_pdfs": sconfig["get_pdfs"]},
        {"regex": sconfig.get("regex")},
        {"pagination": sconfig["pagination"]},
        upsert=True
    )

# Method to return scrapy config based on city
def get_profile(municipality):
    return SCRAPY_CONFIG_COLLECTION.find_one({ "_id": municipality } if municipality else {})
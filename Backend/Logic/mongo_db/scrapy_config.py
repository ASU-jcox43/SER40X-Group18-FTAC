from .connection import DB

SCRAPY_CONFIG_COLLECTION = DB["scrapy_config"]

# Method that inserts or upates an already existing scrapy config
def update_config(municipality: str, sconfig: dict):
    SCRAPY_CONFIG_COLLECTION.update_one(
        filter={"_id": municipality},
        update={"$set": {k: sconfig[k] for k in sconfig.keys()}},
        upsert=True
    )

# Method to return scrapy config based on city
def get_config(municipality: str | None = None, num_results:int = 1) -> list[dict]:
    return SCRAPY_CONFIG_COLLECTION.find({ "_id": municipality } if municipality else {}).limit(num_results).to_list()
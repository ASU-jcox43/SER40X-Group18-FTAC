from .connection import DB
from datetime import datetime, timedelta, timezone

SCRAPY_CONFIG_COLLECTION = DB["scrapy_config"]

# Method that inserts or upates an already existing scrapy config
def update_config(municipality: str, sconfig: dict):
    SCRAPY_CONFIG_COLLECTION.update_one(
        filter={"_id": municipality},
        update={"$set": {k: sconfig[k] for k in sconfig.keys()}},
        upsert=True
    )

def get_config_list(num_results:int = 1) -> list[dict]:
    return SCRAPY_CONFIG_COLLECTION.find({}, {"_id": 0}).to_list()

# Method to return scrapy config based on city
def get_config(municipality: str) -> list[dict]:
    return SCRAPY_CONFIG_COLLECTION.find_one(filter={"_id": municipality})

def get_daily_document_update() -> list[str]:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return SCRAPY_CONFIG_COLLECTION.find(
        {"update_at": {"$elemMatch": {
            "$gte": today_start,
            "$lt": today_start + timedelta(days=1)
            }}}
    ).distinct("_id")
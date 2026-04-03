from .connection import DB
from datetime import datetime

SCRAPY_CONFIG_COLLECTION = DB["scrapy_config"]

# Method that inserts or upates an already existing scrapy config
def update_config(municipality: str, sconfig: dict):
    update_at = sconfig.get("update_at")

    if not update_at:
        update_days = get_update_days()
        sconfig['update_at'] = [min(range(len(update_days))[1:], key=lambda i: update_days[i])]
    else:
        sconfig['update_at'] = [
            datetime(datetime.today().year, d['month'], d['day']).timetuple().tm_yday
            for d in sconfig["update_at"]
        ]

    if len(sconfig['update_at']) == 1:
        sconfig['update_at'] += [((sconfig['update_at'][0] + 183) % 366) + 1]

    SCRAPY_CONFIG_COLLECTION.update_one(
        filter={"_id": municipality},
        update={"$set": {k: sconfig[k] for k in sconfig.keys()}},
        upsert=True
    )

def get_config_list(num_results:int = 1) -> list[dict]:
    return list(SCRAPY_CONFIG_COLLECTION.find(limit=num_results).to_list())

# Method to return scrapy config based on city
def get_config(municipality: str) -> dict:
    return dict(SCRAPY_CONFIG_COLLECTION.find_one(filter={"_id": municipality}))

def get_config_list_with_id(num_results:int = 1) -> list[dict]:
    return SCRAPY_CONFIG_COLLECTION.find({}).to_list()

def get_daily_document_update() -> list[str]:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    return SCRAPY_CONFIG_COLLECTION.find(
        {"update_at": {"$elemMatch": {
            "$gte": today_start,
            "$lt": today_start + timedelta(days=1)
            }}}
    ).distinct("_id")
    
    return list(SCRAPY_CONFIG_COLLECTION.find(
        {"update_at": {"$elemMatch": {"$eq": datetime.now().timetuple().tm_yday}}}
    ))

def get_update_days() -> list:
    pipeline = [
        {"$unwind": "$update_at"},
        {"$group": {"_id": "$update_at", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    
    results = list(SCRAPY_CONFIG_COLLECTION.aggregate(pipeline))
    
    if not results:
        return []
    
    max_value = results[-1]["_id"]
    counts = [0] * (max_value + 1)
    
    for doc in results:
        counts[doc["_id"]] = doc["count"]
    
    return counts

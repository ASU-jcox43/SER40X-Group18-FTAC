from .connection import DB

SCRAPY_CONFIG_COLLECTION = DB["scrapy_output"]

def update_links(municipality:str, urls:list[str]):
    SCRAPY_CONFIG_COLLECTION.update_one(
        filter={"_id": municipality},
        update={"$set": {
            "start_urls": urls,
            "valid": False
            }
        }
    )
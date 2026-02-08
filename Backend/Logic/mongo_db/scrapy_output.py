from .connection import DB

SCRAPY_OUTPUT_COLLECTION = DB["scrapy_output"]

def update_links(municipality:str, urls:list[str]):
    SCRAPY_OUTPUT_COLLECTION.update_one(
        filter={"_id": municipality},
        update={"$set": {
            "start_urls": urls,
            "valid": False
            }
        }
    )

def remove_link(municipality:str, url:str):
    SCRAPY_OUTPUT_COLLECTION.update_one(
        filter={"_id": municipality},
        update={
            "$pull": {"urls": url}
        }
    )

def add_link(municipality:str, url:str):
    SCRAPY_OUTPUT_COLLECTION.update_one(
        filter={"_id": municipality},
        update={
            "$addToSet": {"urls": url}
        }
    )

def get_links(municipality:str) -> list:
    document = SCRAPY_OUTPUT_COLLECTION.find_one(filter={"_id": municipality})
    return document["urls"] if document else None
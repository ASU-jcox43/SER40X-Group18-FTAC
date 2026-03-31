# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient

class DocumentScraperPipeline:
    MONGO_DB = MongoClient("mongodb://ftac-mongo:27017").get_database("CapstoneDB")
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.municipality_name = crawler.spider.municipality_name

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    def process_item(self, item):
        # db.scrapy_output.updateOne({"_id": self.municipality_name}, {$push: {"links": ItemAdapter(item).asdict()}, $set: {"valid": False}})
        item_dict = ItemAdapter(item).asdict()
        self.MONGO_DB["scrapy_output"].update_one(
            filter={"_id": self.municipality_name},
            update={
                "$push": {"urls": {
                    "name": item_dict['name'],
                    "number": item_dict['number'],
                    "year": item_dict['year'],
                    "url": item_dict['url']
                    }},
                "$set": {"valid": False}
            },
            upsert=True
        )
        return item

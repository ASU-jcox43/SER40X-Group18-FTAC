import scrapy


class DocumentscraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains = ["calgary.ca"]
    start_urls = ["https://calgary.ca"]

    def parse(self, response):
        pass

from .document_scraper.spiders.DocumentScraper import DocumentScraperSpider
from scrapy.crawler import Crawler
from scrapy.utils.reactor import install_reactor
import asyncio

def run_document_scraper(*configs: dict):
    install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")

    async def run_document_scraper_wrapped():
        for config in configs:
            crawler = Crawler(DocumentScraperSpider)
            await crawler.crawl_async(config=config)

    asyncio.run(run_document_scraper_wrapped())
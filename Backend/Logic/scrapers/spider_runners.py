from .document_scraper.spiders.DocumentScraper import DocumentScraperSpider
from scrapy.crawler import AsyncCrawlerRunner
from scrapy.utils.defer import deferred_f_from_coro_f
from scrapy.utils.reactor import install_reactor
from twisted.internet.task import react
import sys

REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

async def run_document_scraper(*configs:dict):
    if REACTOR not in sys.modules:
        install_reactor(REACTOR)

    async def run_document_scraper_wrapped(reactor, config:dict):
        await AsyncCrawlerRunner().crawl(DocumentScraperSpider)
    
    for config in configs:
        react(deferred_f_from_coro_f(run_document_scraper_wrapped), [config])
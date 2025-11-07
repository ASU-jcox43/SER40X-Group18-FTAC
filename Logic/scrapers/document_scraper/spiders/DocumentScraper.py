import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http.response import Response
import re

class DocumentScraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains: list[str] = []
    start_urls: list[str] = []
    doc_count: int = 0
    layers: int
    get_pdfs: bool
    rex: str | re.Pattern[str] | None

    def __init__(self, start_url: str, layers: int, get_pdfs: bool, rex: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [re.findall(r"(?<=.)\w*.ca(?=\W)", start_url)[0]]
        self.layers = layers
        self.get_pdfs = get_pdfs
        self.rex = re.compile(rex) if rex else None

    def parse(self, response: Response):
        if self.rex is not None:
            self.rex = re.compile(self.rex)
        yield scrapy.Request(response.url, callback=self.parse_step, cb_kwargs=dict(layer=self.layers))

    def parse_step(self, response: Response, layer: int):
        # Check the URL and yield it if it is a PDF.
        # You will know when you are visiting a PDF when you get a response body that starts with '%PDF-' 
        if response.body.startswith(b'%PDF-') or (layer == 0 and not self.get_pdfs):
            self.doc_count = self.doc_count + 1
            yield {self.doc_count: response.url}
        elif layer > 0:
            links = response.xpath('//@href').getall()
            for link in links:
                if not (self.rex is not None and self.rex.search(link) is None):
                    yield scrapy.Request(response.urljoin(link), callback=self.parse_step, cb_kwargs=dict(layer=layer - 1))

async def run_document_scraper(start_url: str, layers: int=1, get_pdfs: bool=True, rex: str|None=None) -> str:
    """
    :param start_url:
    :param layers: number of clicks that you need to get from the start url to any bylaw PDF
    :param get_pdfs: disable if the bylaw text is not within PDFs
    :param rex: Links must contain a match using this regular expression in order to be traversed after the start url. The default value will match everything.
    :return: path to the extracted links
    """
    municipality = re.findall(r"(?<=.)\w*(?=\.ca\W)", start_url)[0]
    export_to = f"Service/Links/{municipality}_items.json"
    process = CrawlerProcess(
        settings={
            "FEEDS": {
                export_to: {"format": "json"},
            },
        }
    )

    process.crawl(DocumentScraperSpider, start_url=start_url, layers=layers, get_pdfs=get_pdfs, rex=rex)
    process.start()  # the script will block here until the crawling is finished
    process.stop()
    return export_to
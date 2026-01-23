import scrapy
from scrapy.http.response import Response
import re
from scrapy.item import Item, Field

class DocumentScraperItem(Item):
    url = Field()

class DocumentScraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains: list[str] = []
    start_urls: list[str] = None
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
        yield scrapy.Request(response.url, callback=self.parse_step, cb_kwargs=dict(layer=int(self.layers)))

    def parse_step(self, response: Response, layer: int):
        # Check the URL and yield it if it is a PDF.
        # You will know when you are visiting a PDF when you get a response body that starts with '%PDF-' 
        if response.body.startswith(b'%PDF-') or (layer == 0 and not self.get_pdfs):
            self.doc_count = self.doc_count + 1
            yield DocumentScraperItem(url=response.url)
        elif layer > 0:
            links = response.xpath('//@href').getall()
            for link in links:
                if not (self.rex is not None and self.rex.search(link) is None):
                    yield scrapy.Request(response.urljoin(link), callback=self.parse_step, cb_kwargs=dict(layer=layer - 1))
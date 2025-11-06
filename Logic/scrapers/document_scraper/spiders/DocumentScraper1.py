import scrapy
from scrapy.http.response import Response
from scrapy.linkextractors import LinkExtractor
import re

class Documentscraper1Spider(scrapy.Spider):
    name = "DocumentScraper1"
    allowed_domains: list[str] = ["antigonishcounty.ca", "calgary.ca", "mississauga.ca", "ottawa.ca", "york.ca"]
    start_urls: list[str] = ["https://www.calgary.ca/bylaws/city-bylaw-library.html"]
    doc_count: int = 0
    #number of clicks that you need to get from the start url to any bylaw PDF
    layers: str = 1
    #disable if the bylaw text is not within PDFs
    get_pdfs: bool = False
    #Links must contain a match using this regular expression in order to be traversed after the start url.
    #An empty string value will match everything.
    rex = r"Download"

    def parse(self, response: Response):
        if self.rex != r"":
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
                if not (self.rex != r"" and self.rex.search(link) == None):
                    yield scrapy.Request(response.urljoin(link), callback=self.parse_step, cb_kwargs=dict(layer=layer - 1))
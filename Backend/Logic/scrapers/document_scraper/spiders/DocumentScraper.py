import scrapy
from scrapy.http.response import Response
import re
from scrapy.item import Item, Field

class DocumentScraperItem(Item):
    url = Field()

class DocumentScraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains: list[str] = []
    municipality_name: str
    start_urls: list[str] = None
    doc_count: int = 0
    layers: int
    get_pdfs: bool
    regex: str | re.Pattern[str] | None
    xpath: str | None

    def __init__(self, start_url: str, layers: int, get_pdfs: bool, regex: str | None = None, xpath: str | None = None, municipality_name: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [re.findall(r"(?<=\/\/)[\w.]*?(?=\/\W?)", start_url)[0]]
        self.allowed_domains[0] = self.allowed_domains[0][4:] if self.allowed_domains[0].startswith('www.') else self.allowed_domains[0]
        print(f"\n\nallowed domains = {self.allowed_domains}\n\n")

        if municipality_name:
            self.municipality_name = municipality_name
        else:
            self.municipality_name = re.findall(r"(?<=\/\/)[\w.]*?(?=\.\w*\/\W?)", start_url)[0]
            self.municipality_name = self.municipality_name[4:] if self.municipality_name.startswith('www.') else self.municipality_name
            self.municipality_name = self.municipality_name[:-2] if self.municipality_name.endswith('.qc') else self.municipality_name
        
        self.layers = layers
        self.get_pdfs = get_pdfs
        self.regex = re.compile(regex) if regex else None
        self.xpath = xpath
    
    def parse(self, response: Response):
        yield scrapy.Request(response.url, callback=self._parse_step, cb_kwargs=dict(layer=int(self.layers)))

    def _parse_step(self, response, layer: int):
        # Check the URL and yield it if it is a PDF.
        # You will know when you are visiting a PDF when you get a response body that starts with '%PDF-' 
        if response.body.startswith(b'%PDF-') or (layer == 0 and not self.get_pdfs):
            self.doc_count = self.doc_count + 1
            yield DocumentScraperItem(url=response.url)
        elif layer > 0:
            links = response.xpath('//@href').getall()
            yield scrapy.Request(response.url, callback=self._request_next_links, cb_kwargs=dict(links=links, layer=layer, decrease_layer=True))

            if self.xpath:
                next_page_links = response.xpath(self.xpath).getall()
                yield scrapy.Request(response.url, callback=self._request_next_links, cb_kwargs=dict(links=next_page_links, layer=layer, decrease_layer=False))
    
    def _request_next_links(self, response, links: list[str], layer: int, decrease_layer: bool):
        for link in links:
            if not self.regex or self.regex.search(link):
                print(f'Match = {link}')
                try:
                    yield scrapy.Request(response.urljoin(link), callback=self._parse_step, cb_kwargs=dict(layer=layer - (1 if decrease_layer else 0)))
                except ValueError:
                    print(f'invalid link skipped: "{link}"')
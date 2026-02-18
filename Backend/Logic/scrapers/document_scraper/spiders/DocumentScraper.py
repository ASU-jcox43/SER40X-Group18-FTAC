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
    rex: str | re.Pattern[str] | None
    next_page_selector: str | None

    def __init__(self, start_url: str, layers: int, get_pdfs: bool, rex: str | None = None, next_page_selector: str | None = None, municipality_name: str | None = None, **kwargs):
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
        self.rex = re.compile(rex) if rex else None
        self.next_page_selector = next_page_selector

    #@classmethod
    #def from_crawler(cls, crawler, *args, **kwargs):
    #    spider = super().from_crawler(crawler, *args, **kwargs)
    #    spider.settings.set("FEEDS", {f'/scrapy_output/{spider.municipality_name}.csv': {'format': 'csv'}}, priority="spider")
    #    return spider
    
    def parse(self, response: Response):
        if self.rex:
            self.rex = re.compile(self.rex)
        if self.next_page_selector:
            print(f"\n({self.next_page_selector}) NEXT PAGE {response.xpath(self.next_page_selector).getall()}")
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
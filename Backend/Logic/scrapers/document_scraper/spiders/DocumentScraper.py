import scrapy
import logging
from scrapy.http.response import Response
import re
import ast
from scrapy.item import Item, Field

logger = logging.getLogger("scraper")

class DocumentScraperItem(Item):
    url = Field()

class DocumentScraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains: list[str] = []
    start_urls: list[str] = []
    municipality_name: str
    layers: int
    get_pdfs: bool
    layer_filter_regex: str | re.Pattern[str] | None = None
    layer_filter_xpath: str | None = None
    next_page_filter_regex: str | re.Pattern[str] | None = None
    next_page_filter_xpath: str | None = None
    doc_count: int = 0

    #def __init__(self, start_url: str, layers: int, get_pdfs, regex: str | None = None, xpath: str | None = None, municipality_name: str | None = None, **kwargs):
    def __init__(self, config: dict, **kwargs):
        super().__init__(**kwargs)
        print(config)
        config = ast.literal_eval(config)

        logging.getLogger('scrapy.core.engine').setLevel(logging.WARNING)
        logging.getLogger('scrapy.core.scraper').setLevel(logging.WARNING)
        logging.getLogger('scrapy.utils.log').setLevel(logging.WARNING)
        logging.getLogger('scrapy.addons').setLevel(logging.WARNING)
        logging.getLogger('scrapy.middleware').setLevel(logging.WARNING)
        logging.getLogger('scrapy.downloadermiddlewares.offsite').setLevel(logging.WARNING)
        logging.getLogger('scrapy.dupefilters').setLevel(logging.WARNING)
        logging.getLogger('scrapy.extensions.logstats').setLevel(logging.WARNING)
        logging.getLogger('scrapy.statscollectors').setLevel(logging.INFO)

        # pymongo normally prints a lot of distracting DEBUG level messages
        logging.getLogger('pymongo.topology').setLevel(logging.WARNING)
        logging.getLogger('pymongo.connection').setLevel(logging.WARNING)
        logging.getLogger('pymongo.command').setLevel(logging.WARNING)
        logging.getLogger('pymongo.serverSelection').setLevel(logging.WARNING)

        self.start_urls.extend(config['start_urls'])

        if config.get('allowed_domains'):
            self.allowed_domains = config['allowed_domains']
        else:
            self.allowed_domains = [re.findall(r"(?<=\/\/)[\w.]*(?=\/\W?)", start_url)[0] for start_url in self.start_urls]

        self.municipality_name = config['municipality_name']
        
        self.layers = config['layers']
        self.get_pdfs = config['get_pdfs']

        if config.get('layer_filter'):
            self.layer_filter_regex = config.get('layer_filter').get('regex')
            if self.layer_filter_regex:
                self.layer_filter_regex = re.compile(self.layer_filter_regex)
            self.layer_filter_xpath = config.get('layer_filter').get('xpath')
        
        if config.get('next_page_filter'):
            self.next_page_filter_regex = config.get('next_page_filter').get('regex')
            if self.next_page_filter_regex:
                self.next_page_filter_regex = re.compile(self.next_page_filter_regex)
            self.next_page_filter_xpath = config.get('next_page_filter').get('xpath')
    
    def parse(self, response: Response):
        yield scrapy.Request(response.url, callback=self._parse_step, cb_kwargs=dict(layer=int(self.layers)))

    def _parse_step(self, response, layer: int):
        # Check the URL and yield it if it is a PDF.
        # You will know when you are visiting a PDF when you get a response body that starts with '%PDF-'

        logger.info(f'[ L {layer} ({response.status}) {response.urljoin(response.url)} ]')

        if response.body.startswith(b'%PDF-') or (layer == 0 and not bool(self.get_pdfs)):
            logger.info(f'\tSCRAPED {response.url}')
            self.doc_count = self.doc_count + 1
            yield DocumentScraperItem(url=response.url)
        elif layer > 0:
            layer_links: list[str] = response.xpath(self.layer_filter_xpath or '//@href').getall()
            next_page_links = []

            if self.layer_filter_regex:
                layer_links = list(filter(lambda l: self.layer_filter_regex.search(l), layer_links))

            if self.next_page_filter_xpath or self.next_page_filter_regex:
                next_page_links = response.xpath(self.next_page_filter_xpath or '//@href').getall()
            
            if self.next_page_filter_regex:
                next_page_links = list(filter(lambda l: self.next_page_filter_regex.search(l), next_page_links))
            
            layer_links.extend(next_page_links)
            
            for link in layer_links:
                next_layer = layer - (0 if link in next_page_links else 1)
                if link in next_page_links:
                    logger.info(f'\tNEXT {response.urljoin(link)}')
                else:
                    logger.info(f'\t     {response.urljoin(link)}')
                try:
                    yield scrapy.Request(response.urljoin(link), callback=self._parse_step, cb_kwargs=dict(layer=next_layer))
                except ValueError:
                    logger.info(f'invalid link skipped: {link}')
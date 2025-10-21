import scrapy
from scrapy.http.response import Response
from scrapy.linkextractors import LinkExtractor

class Documentscraper1Spider(scrapy.Spider):
    name = "DocumentScraper1"
    allowed_domains: list[str] = ["mississauga.ca"]
    start_urls: list[str] = ["https://www.mississauga.ca/council/by-laws/"]
    pdf_count: int = 0
    #number of clicks that you need to get from the start url to any bylaw PDF
    layers: int = 2

    def parse(self, response: Response):
        response.follow(response, callback=self.parse_step, meta={'layer': str(self.layers)})

    def parse_step(self, response: Response):
        layer = int(response.meta['layer'])
        # Check the URL and yield it if it is a PDF. You will know when you are visiting a PDF when one of the following conditions are met:
        #   1. the URL of the current page ends with ".pdf"
        #   2. there is "Content-Type: application/pdf" in the response header
        if response.url.lower().endswith(".pdf") or ("Content-Type" in response.headers and response.headers["Content-Type"] == b"application/pdf"):
            self.pdf_count = self.pdf_count + 1
            yield {self.pdf_count: response.url}
        elif layer > 0:
            link_extractor = LinkExtractor(allow_domains=allowed_domains)
            links = link_extractor.extract_links(response)
            for link in links:
                yield response.follow(link, callback=self.parse_step, meta={'layer': layer - 1})
        #All PDFs will be added by check() to pdfs[] and any other pages will be ignored

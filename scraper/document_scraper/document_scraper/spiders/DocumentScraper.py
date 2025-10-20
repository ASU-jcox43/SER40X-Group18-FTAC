import scrapy
from scrapy.http.response import Response


class DocumentscraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains: list[str] = ["yellowknife.ca"]
    start_urls: list[str] = ["https://www.yellowknife.ca/Bylaws/Bylaw?_mid_=34596"]
    pdf_count: int = 0

    def parse(self, response: Response):
       #check if any urls are PDFs by calling check() on them
        for url in response.xpath("//@href").getall():
            if self.allowed_domains[0] in url or url.startswith('/'):
                print(f'following {url}')
                yield response.follow(url, callback=self.check)

        #All PDFs will be added by check() to pdfs[] and any other pages will be ignored
    
    def check(self, response: Response):
        # Check the URL and yield it if it is a PDF. You will know when you are visiting a PDF when one of the following conditions are met:
        #   1. the URL of the current page ends with ".pdf"
        #   2. there is "Content-Type: application/pdf" in the response header
        print(f'checking {response.url}: {response.url.endswith(".pdf")}, {response.headers["Content-Type"] if "Content-Type" in response.headers else "no"}')
        if response.url.endswith(".pdf") or ("Content-Type" in response.headers and response.headers["Content-Type"] == b"application/pdf"):
            self.pdf_count = self.pdf_count + 1
            print(f'about to yield {response.url}')
            yield {self.pdf_count: response.url}

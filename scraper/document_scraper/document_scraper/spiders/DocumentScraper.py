import scrapy
from scrapy.http.response import Response


class DocumentscraperSpider(scrapy.Spider):
    name = "DocumentScraper"
    allowed_domains: list[str] = ["yellowknife.ca"]
    start_urls: list[str] = ["https://www.yellowknife.ca/en/index.aspx"]
    visited_urls: set[str] = set()
    pdfs: dict[int, str] = {}
    pdf_count: int = 0
    next_urls: list[str] = []

    def parse(self, response: Response):
        # Use BFS to traverse the entire website of municipality X

        # Mark the current URL as visited
        self.visited_urls.add(response.url)

        # Store all URLs of PDFs visited in pdfs. You will know when you are visiting a PDF if one of the following conditions are met:
        #   1. the URL of the current page ends with ".pdf"
        #   2. there is "Content-Type: application/pdf" in the response header
        if response.url.endswith(".pdf") or (
            "Content-Type" in response.headers
            and response.headers["Content-Type"] == b"application/pdf"
        ):
            self.pdfs[self.pdf_count] = response.url
            self.pdf_count = self.pdf_count + 1

        # append all links on the current page that stay inside of the domain and have not been visited to next_urls

        self.next_urls.extend(
            list(
                filter(
                    lambda s: s not in self.visited_urls
                    and (self.allowed_domains[0] in s or s.startswith("/")),
                    response.xpath("//@href").getall(),
                )
            )
        )

        print(f"visit all pages linked to by {response.url}")

        # Visit all pages linked to by the current page
        if self.next_urls != []:
            yield response.follow(self.next_urls.pop(0), callback=self.parse)
        else:
            yield self.pdfs

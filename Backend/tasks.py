from celery import Celery
import subprocess
from Logic.scrapers.document_scraper.spiders.DocumentScraper import *

document_scraper_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@document_scraper_app.task
def run_document_scraper(start_url: str, layers: int=1, get_pdfs: bool=True, rex: str|None=None):
    name_regex = r"(?<=.)\w*(?=\.ca\W)"
    output_path = f'Service/Links/{re.findall(name_regex, start_url)[0]}.json'
    command = [
        'scrapy', 'runspider',
        '-a', f'start_url={start_url}',
        '-a', f'layers={layers}',
        '-a', f'get_pdfs={get_pdfs}',
        '-a', f'rex={rex}',
        'Logic/scrapers/document_scraper/spiders/DocumentScraper.py',
        '-O', f'{output_path}'
    ]
    subprocess.run(command, text=True)
    return output_path
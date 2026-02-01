from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery
import os
import subprocess
from .Logic.scrapers.document_scraper.spiders.DocumentScraper import *
from .Logic.OCRProcessor.ocr_processor import process_pdfs
from .Logic.extraction.text_extraction import extract
from .Logic.mongo_db.scrapy_config import update_config, get_config
api_app = FastAPI()

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO: specify the allow_origins (frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

class ScrapyConfig(BaseModel):
    start_url: str
    layers: int
    get_pdfs: bool | str
    regex: str | None = None

class PostExtractDocs(BaseModel):
    urls: list[str] # List of document urls

@api_app.post("/ingest-docs")
async def ingest_docs(req:ScrapyConfig):
    @celery_app.task
    def run_document_scraper(start_url: str, layers: int=1, get_pdfs: bool=True, rex: str|None=None):
        name_regex = r"(?<=.)\w*(?=\.ca\W)"
        output_path = f'{re.findall(name_regex, start_url)[0]}.csv'
        os.chdir('Backend/Logic/scrapers')
        command = [
            'scrapy', 'crawl',
            '-a', f'start_url={start_url}',
            '-a', f'layers={layers}',
            '-a', f'get_pdfs={get_pdfs}',
            '-a', f'rex={rex}',
            'DocumentScraper'
        ]
        subprocess.run(command, text=True)
        os.chdir('../../..')
        return output_path
    return run_document_scraper(req.start_url, layers=req.layers, get_pdfs=req.get_pdfs, rex=req.regex)

@api_app.post("/extract")
async def extract_docs(req:PostExtractDocs):
    process_pdfs('Logic/OCRProcessor/bylawDocuments')
    extract()
    return "extraction started"

@api_app.get("/extract")
async def search_docs(
    page: int | None = 0,
    url: str | None = None,
    municipality: str | None = None,
    title: str | None = None,
    category: str | None = None
    ):
    print(f'page={page}\nurl={url}\nmunicipality={municipality}\ntitle={title}\ncategory={category}')
    return [ #TODO replace dummy data with database query
        {"municipality":"Calgary",        "url":"calgary.ca/bylaw2"},
        {"municipality":"Mississauga",    "url":"mississauga.ca/bylaws/5802.pdf"},
        {"municipality":"Vancouver",      "url":"vancouver.ca/bylaws/325.pdf"},
        {"municipality":"Oakville",       "url":"oakville.ca/bylaws/9011.pdf"},
        {"municipality":"Toronto",        "url":"toronto.ca/bylaws/5802.pdf"},
        {"municipality":"Quebec City",    "url":"ville.quebec.qc.ca/bylaws/businessess3/40.html"},
        {"municipality":"York",           "url":"york.ca/bylaws/36.html"}
    ]

@api_app.get("/scrapy_config")
async def search_configs(municipality: str | None = None):
    return get_config(municipality)

@api_app.put("/scrapy_config")
async def edit_config(req: ScrapyConfig, municipality: str):
    update_config({
        "_id": municipality,
        "start_url": req.start_url,
        "layers": req.layers,
        "get_pdfs": req.get_pdfs,
        "regex": req.regex,
    })
    return f"updated {municipality}"
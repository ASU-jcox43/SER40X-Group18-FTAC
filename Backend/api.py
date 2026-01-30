from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from .tasks import *
from fastapi.middleware.cors import CORSMiddleware
api_app = FastAPI()

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO: specify the allow_origins (frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PostIngestDocs(BaseModel):
    start_url: str
    layers: int
    get_pdfs: bool | str
    regex: str | None = None

class PostExtractDocs(BaseModel):
    urls: list[str] # List of document urls

@api_app.post("/ingest-docs")
async def ingest_docs(req:PostIngestDocs):
    """
    :return: path to the extracted links Service/Links/municipality_items.json
    """
    return run_document_scraper(req.start_url, layers=req.layers, get_pdfs=req.get_pdfs, rex=req.regex)

@api_app.post("/extract")
async def extract_docs(req:PostExtractDocs):
    print(req)
    run_ocr_and_extraction_process(req.urls)
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
    return search_configs(municipality)
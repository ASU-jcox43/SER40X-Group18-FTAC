# Don't use .venv

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from ..Logic.scrapers.document_scraper.spiders.DocumentScraper import run_document_scraper
app = FastAPI()

class IngestDocsPut(BaseModel):
    start_url: str
    layers: int
    get_pdfs: bool
    regex: str | None = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/ingest-docs")
async def update_item(req:IngestDocsPut):
    """
    :return: path to the extracted links Service/Links/municipality_items.json
    """
    return await run_document_scraper(req.start_url, layers=req.layers, get_pdfs=req.get_pdfs, rex=req.regex)
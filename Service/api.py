# Don't use .venv

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from ..Logic.scrapers.document_scraper.spiders.DocumentScraper import run_document_scraper
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO: specify the allow_origins (frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
 )

class IngestDocsPut(BaseModel):
    start_url: str
    layers: int
    get_pdfs: bool | str
    regex: str | None = None

@app.post("/Frontend/ingest-docs")
async def update_item(req:IngestDocsPut):
    """
    :return: path to the extracted links Service/Links/municipality_items.json
    """
    return await run_document_scraper(req.start_url, layers=req.layers, get_pdfs=req.get_pdfs, rex=req.regex)
# Don't use .venv

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from tasks import *
from Logic.OCRProcessor import OCRProcessor as ocr
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
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

class DocKey(BaseModel):
    municipality: str
    title: str

class PostExtractDocs(BaseModel):
    docs: list[DocKey]

class GetSearchDocs(BaseModel):
    municipality: str
    title: str
    category: str

@app.post("/Frontend/ingest-docs")
async def ingest_docs(req:PostIngestDocs):
    """
    :return: path to the extracted links Service/Links/municipality_items.json
    """
    return run_document_scraper(req.start_url, layers=req.layers, get_pdfs=req.get_pdfs, rex=req.regex)

@app.post("/Frontend/extract")
async def extract_docs(req:PostExtractDocs):
    print(req)
    ocr.process_pdfs("OCRProcessor/bylawDocuments/")
    return "extraction started"

@app.get("/Frontend/extract")
async def search_docs(req:GetSearchDocs):
    pass
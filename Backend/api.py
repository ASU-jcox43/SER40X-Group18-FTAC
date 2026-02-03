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

from Backend.Logic.reports.report_generator import generate_report
from pathlib import Path
from fastapi.responses import FileResponse
import zipfile
import tempfile
from fastapi import Body
from fastapi.responses import StreamingResponse
from io import BytesIO

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
@api_app.post("/Frontend/generate-report")
async def generate_report_endpoint():
    """
    :return: links the frontend can use to download the report files.
    """
    ROOT = Path(__file__).resolve().parent.parent
    analysis_dir = ROOT / "Backend" / "Logic" / "analysis_ready"
    score_file = ROOT / "Backend" / "Logic" / "scoring" / "friendliness_summary.json"
    output_dir = ROOT / "Backend" / "Logic" / "reports" / "generated_reports"
    output_dir.mkdir(exist_ok=True)

    results = []

    for analysis_file in analysis_dir.glob("*.json"):
        report_name = f"{analysis_file.stem}_Report.md"
        output_path = output_dir / report_name

        md_path = generate_report(
            file_path=str(analysis_file),
            score_path=str(score_file),
            output_path=str(output_path)
        )

        file_result = {
            "filename": md_path.name
        }
        results.append(file_result)

    return results

@api_app.get("/Frontend/download-reports")
async def download_reports():
    """
    Returns: makes the backend zip up all the reports, and send it all as a download for the frontend.
    """
    ROOT = Path(__file__).resolve().parent.parent
    reports_dir = ROOT / "Backend" / "Logic" / "reports" / "generated_reports"

    if not reports_dir.exists():
        return {"error": "No reports exist to be downloaded."}

    tmp_dir = Path(tempfile.mkdtemp())
    zip_path = tmp_dir / "reports.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for md_file in reports_dir.glob("*.md"):
            zipf.write(md_file, arcname=md_file.name)

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename="reports.zip"
    )

@api_app.get("/Frontend/list-reports")
async def list_reports():
    """
    Returns: list of reports that are ready to be downloaded for the user.
    """
    ROOT = Path(__file__).resolve().parent.parent
    reports_dir = ROOT / "Backend" / "Logic" / "reports" / "generated_reports"

    if not reports_dir.exists():
        return []

    file_list = []
    for f in reports_dir.glob("*.md"):
        file_list.append({"id": f.name, "name": f.stem.replace("_", " ")})

    return file_list

@api_app.post("/Frontend/download-selected")
async def download_selected(reportIds: list[str] = Body(...)):
    """
    Args:
        reportIds: Takes a list of the report Ids to download.

    Returns: Stream of the zip file of the reports.
    """
    ROOT = Path(__file__).resolve().parent.parent
    reports_dir = ROOT / "Backend" / "Logic" / "reports" / "generated_reports"

    if not reportIds:
        return {"error": "No reports selected."}

    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for report_id in reportIds:
            report_path = reports_dir / report_id
            if report_path.exists() and report_path.is_file():
                zipf.write(report_path, arcname=report_path.name)
    zip_buffer.seek(0)

    reports = StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=selected_reports.zip"}
    )
    return reports

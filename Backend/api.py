from typing import Union
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import os
import subprocess
from .Logic.scrapers.document_scraper.spiders.DocumentScraper import *
from .Logic.OCRProcessor.ocr_processor import process_pdfs
from .Logic.extraction.text_extraction import extract
from .Logic.mongo_db.scrapy_config import update_config, get_config
from .Logic.mongo_db.scrapy_output import get_links, remove_link, add_link
from Backend.Logic.reports.report_generator import generate_report
from pathlib import Path
from fastapi.responses import FileResponse
import zipfile
import tempfile
from fastapi import Body
from fastapi.responses import StreamingResponse
from io import BytesIO
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # execute this before application startup
    yield
    # execute this after application finishes

api_app = FastAPI(lifespan=lifespan)

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO: specify the allow_origins (frontend origin)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapyFilter(BaseModel):
    regex: str | None = None
    xpath: str | None = None

class ScrapyConfig(BaseModel):
    start_urls: list[str] | None = None
    allowed_domains: list[str] | None = None
    layers: int | None = None
    get_pdfs: bool | None = None
    layer_filter: ScrapyFilter | None = None
    next_page_filter: ScrapyFilter | None = None

class PostExtractDocs(BaseModel):
    urls: list[str] # List of document urls

@api_app.post("/ingest-docs")
async def ingest_docs(municipality: str, background_tasks: BackgroundTasks):
    config:dict

    try:
        config = get_config(municipality)[0]
        config['municipality_name'] = config['_id']
        config.pop('_id')
    except IndexError:
        raise HTTPException(status_code=404, detail="municipality not found")
    
    def run_document_scraper(config: dict):
        command = ['scrapy', 'crawl']
        #args = [f'{k}={int(config[k]) if isinstance(config[k], bool) else config[k]}' for k in config.keys()]
        #command.extend([x for a in args for x in ('-a', a)])
        command.extend(['-a', f'config={str(config)}'])
        command.append('DocumentScraper')
        logger.info(f'command = {command}')
        os.chdir('Backend/Logic/scrapers')
        subprocess.run(command, text=True)
        os.chdir('../../..')

    background_tasks.add_task(run_document_scraper, config)
    return "crawl start"

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
    return get_config(municipality, num_results=10)

@api_app.put("/scrapy_config")
async def edit_config(req: ScrapyConfig, municipality: str):
    update_config(municipality,req.model_dump(exclude_unset=True))
    return f"updated {municipality}"

@api_app.get("/scrapy_config/output")
async def get_scrapy_output(municipality: str):
    return get_links(municipality)

@api_app.delete("/scrapy_config/output")
async def remove_scrapy_link(municipality: str, link: str):
    remove_link(municipality,link)
    return f"removed {link} from {municipality}"

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

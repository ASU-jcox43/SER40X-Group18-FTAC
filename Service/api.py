# Don't use .venv

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from Backend.tasks import *
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
from Backend.Logic.reports.report_generator import generate_report
from pathlib import Path
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
    return run_document_scraper(req.start_url, layers=req.layers, get_pdfs=req.get_pdfs, rex=req.regex)

class ReportRequest(BaseModel):
    pass

@app.post("/Frontend/generate-report")
async def generate_report_endpoint(req: ReportRequest):
    """
    :return: links the frontend can use to download the report files.
    """
    ROOT = Path(__file__).resolve().parent.parent
    analysis_dir = ROOT / "Logic" / "analysis_ready"
    score_file = ROOT / "Backend" / "Logic" / "scoring" / "friendliness_summary.json"

    output_dir = ROOT / "Logic" / "reports" / "generated_reports"
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
            "md": str(md_path)
        }
        results.append(file_result)

    return results
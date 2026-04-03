import os
import re
import json
import anthropic
from dotenv import load_dotenv
from Backend.Logic.mongo_db.scrapy_config import get_config_list_with_id, get_config_list
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions, getExtraction
from Backend.Logic.extraction.text_extraction import extractURL

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """
You are a municipal regulatory analyst for food truck businesses.

You will receive JSON data containing keyword-extracted sentences from a legal document.

Your job is to output a markdown report in EXACTLY this format:

# Summary Report for {filename}
**Overall Score:** {x}%
---
## Overview
| Total Categories | Found | Missing |
...
## Category Status
...
## Key Findings
...
## Recommendations
...

Rules:
- Mark a category as Found only if its keyword_contexts entry has data
- Clean up extracted sentences into readable findings
- Never invent information not present in the data
"""

# Path to the reports folder relative to this file's location
REPORTS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", 
    "Backend", "Logic", "reports", "generated_reports"
))

def AI_Generate_Report(doc: dict) -> str:
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Here is the extracted data:\n\n{json.dumps(doc, indent=2)}"
            }
        ]
    )
    return response.content[0].text

def sanitize_filename(file_id: str) -> str:
    # Strip the protocol first (https://, http://)
    name = re.sub(r'^https?://', '', file_id)
    # Replace any character that isn't letters, numbers, dash or underscore
    name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    # Collapse multiple underscores into one
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores
    name = name.strip('_')
    return name

def save_report(doc: dict, report: str):
    filename = sanitize_filename(doc.get("file", "unknown"))
    filepath = os.path.join(REPORTS_DIR, f"{filename}_report.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved: {filepath}")
    
def sort_links():
    configs = get_config_list()
    for config in configs:
        start = config.get("start_urls", "unkown")
        
def display_extractions():
    docs = getAllExtractions()
    for i, doc in enumerate(docs):
        filename = doc["file"]
        print(f"{i}, {filename}")
        
    select_extraction()
        
def select_extraction():
    while True:
        print("Choose an extraction document")
        
        selection = input("Select extraction: ")
        
        file = getExtraction(selection)
        
        if file != None:
            return file

        print("Invalid Selection\n")

if __name__ == "__main__":
    # Step 1 — scrape and extract all URLs from config
    configList = get_config_list_with_id()
    for config in configList:
        start_urls = config.get("start_urls", [])
        url = start_urls[0] if start_urls else None
        if url:
            extractURL(url)
    
    # Step 2 — make sure the reports folder exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    # Step 3 — generate a report for selected document
    doc = display_extractions()

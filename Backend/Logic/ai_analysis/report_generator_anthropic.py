import os
import re
import json
import anthropic
from dotenv import load_dotenv
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions
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
    """Injects the selected text extraced links into the AI system prompt to create a report

    Args:
        doc (dict): The extracted text of the selected document
    """
    
    print("Generating report")
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
    
    save_report(doc, response)
    print("Report Generated")


def save_report(doc: dict, report: str):
    """Saves the report into the file directory Backend/Logic/reports/generated_reports

    Args:
        doc (dict): The extracted text of the selected document
        report (str): The report generated from AI Anthropic
    """
    
    filename = sanitize_filename(doc.get("file", "unknown"))
    filepath = os.path.join(REPORTS_DIR, f"{filename}_report.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report saved: {filepath}")

def sanitize_filename(filename: str) -> str:
    """Clean the filename of the document to make it easier to read

    Args:
        file_id (str): _description_

    Returns:
        str: _description_
    """
    
    # Strip the protocol first (https://, http://)
    name = re.sub(r'^https?://', '', filename)
    # Replace any character that isn't letters, numbers, dash or underscore
    name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    # Collapse multiple underscores into one
    name = re.sub(r'_+', '_', name)
    # Strip leading/trailing underscores
    name = name.strip('_')
    return name
    
def display_extractions():
    docs = getAllExtractions()

    grouped_docs = {
        "pdf": [],
        "txt": [],
        "web": [],
        "bylaw": [],
        "other": []
    }

    # Step 1 — Filter valid docs
    for doc in docs:
        context = doc.get("keyword_contexts", {})

        if not (context and any(context.values())):
            continue

        file_name = doc.get("file", "")
        doc_type = get_doc_type(file_name)

        grouped_docs[doc_type].append(doc)

    # Step 2 — Flatten in preferred order
    ordered_types = ["pdf", "txt", "bylaw", "web", "other"]
    final_docs = []

    index = 0

    for dtype in ordered_types:
        if not grouped_docs[dtype]:
            continue

        print(f"\n=== {dtype.upper()} DOCUMENTS ===")

        for doc in grouped_docs[dtype]:
            print(f"{index}: {doc['file']}")
            final_docs.append(doc)
            index += 1

    return select_extraction(final_docs)

def get_doc_type(file_name: str) -> str:
    file_name = file_name.lower()

    if file_name.startswith("http"):
        return "web"

    if file_name.endswith(".pdf"):
        return "pdf"

    if file_name.endswith(".txt"):
        return "txt"

    if "bylaw" in file_name or "by-law" in file_name:
        return "bylaw"

    return "other"
        
def select_extraction(docs):
    """Function to get the selected input from the user

    Args:
        docs (JSON): The list of docs sorted

    Returns:
        JSON: The selected document from the list of extractions 
    """
    
    while True:
        print("Choose an extraction document")

        try:
            selection = int(input("Select extraction: "))

            if 0 <= selection < len(docs):
                return docs[selection]

        except ValueError:
            pass

        print("Invalid Selection\n")

if __name__ == "__main__":
    # Step 1 — make sure the reports folder exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    # Step 2 — generate a report for selected document
    doc = display_extractions()
    # TODO: Rememeber to uncomment to use the AI
    # AI_Generate_Report(doc)
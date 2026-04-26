import os
import re
import json
import anthropic
from collections import defaultdict
from dotenv import load_dotenv
from Backend.Logic.mongo_db.extraction_collection import getExtraction
from Backend.Logic.mongo_db.profile_collection import getAllProfiles

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
    
def display_profiles():
    """Displays a list of filtered list of extraction and groups extraction docs
    by file type/title

    Returns:
        JSON: Selected document for AI Report generation
    """
    
    profiles = getAllProfiles()

    grouped_docs = defaultdict(list)

    # Filter + group
    for profile in profiles:
        filename = profile["file"]
        
        # Check if extraction version of profile is not empty
        doc = getExtraction(filename)
        context = doc.get("keyword_contexts", {})
        if not (context and any(context.values())):
            continue
        
        title = profile["Title"]
        grouped_docs[title].append(doc)

    # Display groups
    final_docs = []
    index = 0

    for dtype, doc_list in grouped_docs.items():
        print(f"\n=== {dtype.upper()} DOCUMENTS ===")

        for doc in doc_list:
            print(f"{index}: {doc['file']}")
            final_docs.append(doc)
            index += 1

    return select_extraction(final_docs)
        
def select_extraction(docs):
    """Function to get the selected input from the user

    Args:
        docs (JSON): The list of docs sorted

    Returns:
        JSON: The selected document from the list of extractions 
    """
    
    while True:
        print("\nChoose an extraction document")

        try:
            selection = int(input("Select extraction: "))

            if 0 <= selection < len(docs):
                return docs[selection]

        except ValueError:
            pass

        print("Invalid Selection\n")

if __name__ == "__main__":
    # Make sure the reports folder exists
    os.makedirs(REPORTS_DIR, exist_ok=True)
    
    # Display profiles for users to select
    doc = display_profiles()
    
    # Generate report AI
    AI_Generate_Report(doc)
from openai import OpenAI
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import json
import os
import sys

with open("config.json", "r") as f:
    config = json.load(f)

OPENAI_API_KEY = config["openai_api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)

TEMPLATE_PATH = "FTAC Summary Report Template.docx"
OUTPUT_PATH = "Toronto_Report6.docx"

if not os.path.exists(TEMPLATE_PATH):
    print(f"Template not found: {TEMPLATE_PATH}")
    sys.exit(1)

data_path = os.path.join("..", "analysis_ready", "Toronto_Food_Trucks_Copied_And_Pasted.json")
with open(data_path, "r", encoding="utf-8") as f:
    data = json.load(f)

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = ""
    for p in doc.paragraphs:
        text += p.text + "\n"
    return text

def clean_gpt_json(text):
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) > 1:
            text = "\n".join(lines[1:-1])
        else:
            text = ""
    return text

def set_cell_background(cell, fill):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tcPr.append(shd)

def replace_placeholder(paragraph, placeholder, replacement):
    for run in paragraph.runs:
        if placeholder in run.text:
            run.text = run.text.replace(placeholder, str(replacement))

def insert_list_after_placeholder(paragraph, placeholder, items):
    for run in paragraph.runs:
        if placeholder in run.text:
            run.text = run.text.replace(placeholder, "")
            for i, item in enumerate(items):
                if i > 0:
                    run.add_break()
                run.add_text(str(item))

template_text = extract_text_from_docx(TEMPLATE_PATH)

prompt = f"""
You are a report generator. Using the data below, generate a structured report that follows the template.
Return JSON ONLY with keys: overall_score, found_categories, missing_categories, key_findings, recommendations, summary_table.
summary_table should be an array of objects with keys: Category, Found (true/false).
For the score, put a number between 0-100 based on the number of found categories versus total categories.
For key findings, focus on specific information, such as costs of fees, specific distances required, or other information important to the categories.
For recommendations, focus on important missing category information. 

TEMPLATE:
{template_text}

DATA:
{json.dumps(data, indent=2)}
"""

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You generate structured policy reports about municipal regulations. Return JSON only."
            },
            {"role": "user", "content": prompt}
        ]
    )
except Exception as e:
    print("OpenAI request failed:", e)
    sys.exit(1)

report_text = response.choices[0].message.content
cleaned_text = clean_gpt_json(report_text)

try:
    report_json = json.loads(cleaned_text)
except json.JSONDecodeError as e:
    print("Failed to parse JSON from GPT output:", e)
    print("GPT output was:", report_text)
    sys.exit(1)

def fill_template(template_path, output_path, data):
    doc = Document(template_path)

    for p in doc.paragraphs:
        # Single values
        replace_placeholder(p, "{{OVERALL_SCORE}}", data.get("overall_score", ""))

        # Lists
        insert_list_after_placeholder(p, "{{FOUND_CATEGORIES}}", data.get("found_categories", []))
        insert_list_after_placeholder(p, "{{MISSING_CATEGORIES}}", data.get("missing_categories", []))
        insert_list_after_placeholder(p, "{{KEY_FINDINGS}}", data.get("key_findings", []))
        insert_list_after_placeholder(p, "{{RECOMMENDATIONS}}", data.get("recommendations", []))

        # Summary table
        if "{{SUMMARY_TABLE}}" in p.text:
            parent = p._p.getparent()
            index = parent.index(p._p)
            parent.remove(p._p)

            table = doc.add_table(rows=1, cols=2)
            table.rows[0].cells[0].text = "Category"
            table.rows[0].cells[1].text = "Found"

            for row in data.get("summary_table", []):
                r = table.add_row()
                r.cells[0].text = row.get("Category", "")
                found = row.get("Found", False)
                r.cells[1].text = "Yes" if found else "No"
                set_cell_background(r.cells[1], "00FF00" if found else "FF0000")

            parent.insert(index, table._tbl)

    doc.save(output_path)

fill_template(TEMPLATE_PATH, OUTPUT_PATH, report_json)

print("\nReport generated successfully!")
print("Saved as:", OUTPUT_PATH)

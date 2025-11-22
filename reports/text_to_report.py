from openai import OpenAI
from docx import Document
import json
import os
from PyPDF2 import PdfReader

with open("config.json", "r") as f:
    config = json.load(f)

OPENAI_API_KEY = config["openai_api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)

INPUT_FOLDER = "../test documents/"
OUTPUT_FOLDER = "../reports/generated reports/"


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file using PyPDF2."""
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()


def extract_text(file_path: str) -> str:
    """Extract text from either a PDF or txt file."""
    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    else:
        return ""  # this should never happen ideally


def generate_report_for_file(file_path: str, output_docx: str, prompt: str):
    """
    Reads a file, sends it with a prompt to the ChatGPT API,
    receives the output, and saves it as a .docx file.
    """
    text_input = extract_text(file_path)

    if not text_input.strip():
        print(f"Skipping unsupported/empty file: {file_path}")
        return

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that makes reports."},
            {"role": "user", "content": f"{prompt}\n\n---\n{text_input}"}
        ]
    )

    report_text = response.choices[0].message.content

    doc = Document()
    doc.add_paragraph(report_text)
    doc.save(output_docx)

    print(f"Report saved to: {output_docx}")


def process_folder(input_folder: str, output_folder: str, prompt: str):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".txt", ".pdf")):
            txt_path = os.path.join(input_folder, filename)

            name_only = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{name_only}_report.docx")

            generate_report_for_file(txt_path, output_path, prompt)


if __name__ == "__main__":
    with open("report_prompt.txt", "r", encoding="utf-8") as f:
        prompt_text = f.read()

    process_folder(INPUT_FOLDER, OUTPUT_FOLDER, prompt_text)

import json
import re
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import glob
import os


# Get all PDF files in a folder
def get_pdf_files(folder_path):
    # Folder where PDFs are stored
    pdf_folder = "bylawDocuments/"
    pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
    print(f"Files in directory {pdf_files}") # TEST print file path
    return pdf_files or []  # returns empty list if no PDFs

# Check if PDF is scanned or text-based
def is_scanned_pdf(file_path):
    doc = fitz.open(file_path)
    text = "".join([page.get_text() for page in doc])
    return text.strip() == ""  # True if scanned

# Run OCR on scanned PDF
def run_ocr_by_sections(file_path, dpi=300):
    pages = convert_from_path(file_path, dpi=dpi)
    ocr_output = {"file_name": os.path.basename(file_path), "sections": []}

    section_pattern = re.compile(r"^(Section|ARTICLE)\s+\d+", re.IGNORECASE)
    current_section = {"title": "Introduction", "text": ""}

    for page in pages:
        data = pytesseract.image_to_data(page, output_type=pytesseract.Output.DICT)
        for j, word in enumerate(data["text"]):
            if word.strip() == "":
                continue
            # Detect section heading
            if section_pattern.match(word):
                # Save previous section if it has text
                if current_section["text"].strip():
                    ocr_output["sections"].append(current_section)
                # Start new section
                current_section = {"title": word, "text": ""}
            else:
                current_section["text"] += " " + word

    # Append last section
    if current_section["text"].strip():
        ocr_output["sections"].append(current_section)

    return ocr_output


# Save JSON output
def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"JSON saved: {output_path}")


# Main processing function
def process_pdfs(folder_path):
    pdf_files = get_pdf_files(folder_path)
    if not pdf_files:
        print("No PDFs found in folder.")
        return

    for file_path in pdf_files:
        print(f"Processing: {file_path}")
        if is_scanned_pdf(file_path):
            print(f"{file_path}: Scanned PDF → running OCR")
            ocr_data = run_ocr(file_path)
            json_file = os.path.join(folder_path, os.path.basename(file_path).replace(".pdf", "_ocr.json"))
            save_json(ocr_data, json_file)
        else:
            print(f"{file_path}: Text-based PDF → extracting text")
            doc = fitz.open(file_path)
            text = "".join([page.get_text() for page in doc])
            text_data = {"file_name": os.path.basename(file_path), "text": text}
            json_file = os.path.join(folder_path, os.path.basename(file_path).replace(".pdf", "_text.json"))
            save_json(text_data, json_file)


# Run the pipeline
if __name__ == "__main__":
    pdf_folder = "bylawDocuments/"
    process_pdfs(pdf_folder)

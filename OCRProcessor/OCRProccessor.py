import json
import re
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import glob
import os
from unstructured.partition.text import partition_text
from unstructured.partition.pdf import partition_pdf    

import nltk

required_nltk = [
    "punkt",
    "punkt_tab",
    "averaged_perceptron_tagger",
    "averaged_perceptron_tagger_eng"
]

for pkg in required_nltk:
    try:
        nltk.data.find(f"tokenizers/{pkg}")
    except LookupError:
        nltk.download(pkg)


# Get all PDF files in a folder
# Function that retrieves and stores PDF files to a list
def get_pdf_files(folder_path):
    # Folder where PDFs are stored
    pdf_folder = "bylawDocuments/"
    try:
        pdf_files = glob.glob(os.path.join(pdf_folder, "*.pdf"))
        print(f"Files in directory {pdf_files}") # TEST print file path
        return pdf_files or []  # returns empty list if no PDFs
    except Exception as e:
        print(f"Error reading foler {folder_path}: {e}")
        return []

# Check if PDF is scanned or text-based
# Function to check if pdf is scanned (image based)
def is_scanned_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = "".join([page.get_text() for page in doc])
        print(f"{file_path} is image based (scanned)")
        return text.strip() == ""  # True if scanned
    except Exception as e: 
        print(f"Error checking PDF {file_path}: {e}")
        return True

# Run OCR on scanned PDF
# Separates OCR extracted data into sections to organize relevant data from PDF
# organizes the data for JSON format
def run_ocr(file_path, dpi=300):
    try:
        pages = convert_from_path(file_path, dpi=dpi)
    except Exception as e:
        print(f"Error converting to PDF to image {file_path}:{e}")

    ocr_output = {"file_name": os.path.basename(file_path), "sections": []}

    section_pattern = re.compile(r"^(Section|ARTICLE)\s+\d+", re.IGNORECASE)
    current_section = {"title": "Introduction", "text": ""}

    for page in pages:
        try:
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
        except Exception as e:
            print(f"Error running OCR on page {page_num} of {file_path}:{e}")
            continue

    # Append last section
    if current_section["text"].strip():
        ocr_output["sections"].append(current_section)

    return ocr_output

def extract_text(file_path):
    try:
        doc = fitz.open(file_path)
        # Regex matches headings like "Section 1", "SECTION I", "Article 2", etc.
        section_pattern = re.compile(r"^(Section|SECTION|Article|ARTICLE|§)\s*[\w\d\.\-]+", re.IGNORECASE)
        
        output = {"file_name": os.path.basename(file_path), "sections": []}
        current_section = {"title": "Introduction", "text": ""}

        for page in doc:
            text = page.get_text()
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Detect section heading
                if section_pattern.match(line):
                    if current_section["text"]:
                        # Strip trailing newline
                        current_section["text"] = current_section["text"].rstrip("\n")
                        output["sections"].append(current_section)
                    current_section = {"title": line, "text": ""}
                else:
                    # Preserve line breaks for readability
                    if current_section["text"]:
                        current_section["text"] += "\n" + line
                    else:
                        current_section["text"] = line

        if current_section["text"]:
            current_section["text"] = current_section["text"].rstrip("\n")
            output["sections"].append(current_section)

        return output

    except Exception as e:
        print(f"Error extracting text from {file_path}: {e}")
        return {"file_name": os.path.basename(file_path), "sections": []}



# Save JSON output
# Function saves JSON output to JSON Path with proper encoding and formatting
def save_json(data, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"JSON saved: {output_path}")
    except Exception as e:
        print(f"Error saving JSON {output_path}: {e}")


# Main processing function
# Function process pdf image files or text based pdfs
# Utilizes other functions for OCR processing, saving JSON 
def process_pdfs(folder_path):
    pdf_files = get_pdf_files(folder_path)
    if not pdf_files:
        print("No PDFs found in folder.")
        return

    for file_path in pdf_files:
        print(f"\nProcessing: {file_path}")
        try:
            if is_scanned_pdf(file_path):
                print("Detected scanned PDF → running OCR")
                extracted = run_ocr(file_path)
            else:
                print("Detected text-based PDF → extracting text")
                extracted = extract_text(file_path)

            # Pass through Unstructured for cleanup/organization
            structured_data = structure_with_unstructured(extracted, file_path)

            # Save JSON
            json_file = os.path.join(
                folder_path,
                os.path.basename(file_path).replace(".pdf", "_structured.json"),
            )
            save_json(structured_data, json_file)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def structure_with_unstructured(input_data, file_path):
    """
    Takes extracted text or OCR data and uses Unstructured to organize it into structured JSON.
    """
    try:
        # Join all text sections into one long text string for Unstructured
        text_content = ""
        if "sections" in input_data:
            text_content = "\n\n".join(
                f"{sec['title']}\n{sec['text']}" for sec in input_data["sections"]
            )
        elif "text" in input_data:
            text_content = input_data["text"]
        else:
            text_content = str(input_data)

        if not text_content.strip():
            print(f"No text found in {file_path}, skipping structuring.")
            return input_data

        # Use Unstructured to detect layout elements (headings, paragraphs, lists, tables)
        elements = partition_pdf(filename=file_path) if file_path.lower().endswith(".pdf") else partition_text(text=text_content)

        structured = {
            "file_name": input_data["file_name"],
            "elements": [e.to_dict() for e in elements]
        }
        return structured

    except Exception as e:
        print(f"Error structuring file {file_path}: {e}")
        return input_data


# Run the pipeline
if __name__ == "__main__":
    pdf_folder = "bylawDocuments/"
    process_pdfs(pdf_folder) # Generates _ocr.json or _text.json files

    json_file = os.path.join(pdf_folder, "bylawDocumnets/*json")


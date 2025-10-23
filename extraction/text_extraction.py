import os
import json
from PyPDF2 import PdfReader
from extraction_util import cleanText, extractKeywords

# TODO Update for relevant categories and terms
# Define your keyword categories and terms
# Category: Terms []
KEYWORDS = {
    "webpage": [".gov"],
    "checklist": ["checklist"],
    "guide to license": ["guide"],
    "bylaws": ["bylaw"],
    "penalties": ["fine", "fee"],
    "provincial business license": ["provincial business license"],
    "provincial food business license": ["provincial food business license"],
    "municipal business license": ["municipal business license"],
    "municipal food business license": ["municipal food business license"],
    "retail license for CPG": ["consumer packaged good", "CPG"],
    "curbside vending": ["curbside vending"],
    "parking fees": ["parking fee"],
    "noise bylaws": ["noise", "noise bylaw", "sound"],
    "traffic bylaws": ["traffic bylaw"],
    "operation hours": ["operation hours", "hours"],
    "branded consumer goods": ["branding", "branded consumer goods"],
    "private property operation": ["private property"],
    "proximity regulations": ["proximity regulation"],
    "min distance to restaurant": ["distance to restaurants"],
    "min distance to food truck": ["food truck", "from food truck"],
    "non-food service proximity restrictions": ["proximity regulation", "non-food service proximity"],
    "min distance proximity from other business": ["proximity to other business"],
    "num food trucks allowed in geographic area": ["number of food trucks allowed", "food trucks can be in"],
    "parking locations": ["designated parking", "allowed parking", "parking allowed"],
    "additional private restrictions": ["private restrictions"],
    "name of local authority": ["local authority"],
    "insurance requirements": ["insurance"],
    "physical requirements for trucks": ["trucks must have"],
    "exterior appearance guidelines": ["appearance", "exterior look"],
}

FILEPATH = os.path.join("..", "test documents")
SAVEPATH = os.path.join("..", "analysis_ready")


# TODO: Change the output of a analysis ready json to a txt file if needed
def extractTXT(filename):
    txtPath = os.path.join(FILEPATH, filename)
    # Read plain text
    with open(txtPath, "r", encoding="utf-8") as file:
        txtRaw = file.read()

    if not txtRaw:
        print(
            "[Warning] No text could be extracted from the TXT. It may be scanned (use OCR)."
        )
        return

    txtCleaned = cleanText(txtRaw)
    txtResults = {}

    for category, terms in KEYWORDS.items():
        txtResults[category] = extractKeywords(txtCleaned, terms)

    txtJSON = {
        "file": filename,
        "keyword_contexts": txtResults,
    }

    os.makedirs(SAVEPATH, exist_ok=True)
    saveFile = os.path.join(SAVEPATH, filename.replace(".txt", ".json"))
    with open(saveFile, "w", encoding="utf-8") as saveFile:
        json.dump(txtJSON, saveFile, indent=2)

    print("Extracted txt file")


def extractPDF(filename):
    pdfPath = os.path.join(FILEPATH, filename)

    # Read PDF file
    with open(pdfPath, "rb") as pdf_file:
        reader = PdfReader(pdf_file)
        pdfRaw = ""
        for page in reader.pages:
            pdfRaw += page.extract_text() or ""

    if not pdfRaw.strip():
        print(
            "[Warning] No text could be extracted from the PDF. It may be scanned (use OCR)."
        )
        return

    # Clean and analyze
    pdfCleaned = cleanText(pdfRaw)
    pdfResults = {}

    for category, terms in KEYWORDS.items():
        pdfResults[category] = extractKeywords(pdfRaw, terms)

    pdfJSON = {
        "file": filename,
        "keyword_contexts": pdfResults,
    }

    os.makedirs(SAVEPATH, exist_ok=True)
    saveFile = os.path.join(SAVEPATH, filename.replace(".pdf", ".json"))
    with open(saveFile, "w", encoding="utf-8") as saveFile:
        json.dump(pdfJSON, saveFile, indent=2)

    print("Extracted pdf file")


if __name__ == "__main__":
    for file_name in os.listdir(FILEPATH):
        if file_name.lower().endswith(".txt"):
            extractTXT(file_name)
        elif file_name.lower().endswith(".pdf"):
            extractPDF(file_name)

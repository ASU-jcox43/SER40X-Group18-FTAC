import os
import json
from PyPDF2 import PdfReader
from extraction_util import accessDocuments, cleanText, extractKeywords

# TODO Update for relevant categories and terms
# Define your keyword categories and terms
# Category: Terms []
KEYWORDS = {
    "Permit Documents": ["permit", "authorization", "inspection"],
    "Financial Documents": ["invoice", "payment", "tax"],
    "Legal Documents": ["contract", "regulation", "compliance"],
}

# TODO: Change to path where documents can be analyzed
FILEPATH = os.path.join("..", "SER40X-Group18-FTAC", "classifier", "test documents")
SAVEPATH = os.path.join("..", "SER40X-Group18-FTAC", "extraction", "analysis_ready")


# TODO: Change the output of a analysis ready json to a txt file if needed
def extractTXT(filename):
    txtPath = os.path.join(FILEPATH, filename)
    txtRaw = accessDocuments(txtPath)
    if not txtRaw:
        exit()

    txtCleaned = cleanText(txtRaw)

    txtResults = {}
    for category, terms in KEYWORDS.items():
        txtResults[category] = extractKeywords(txtCleaned, terms)

    # Can change to a different format
    # Used JSON because i'm familiar with it
    txtJSON = {
        "file": os.path.basename(filename),
        "keyword_contexts": txtResults,
    }

    print(json.dumps(txtJSON, indent=4))

    os.makedirs(SAVEPATH, exist_ok=True)
    saveFile = os.path.join(SAVEPATH, filename.replace(".txt", ".json"))
    with open(saveFile, "w", encoding="utf-8") as saveFile:
        json.dump(txtJSON, saveFile, indent=2)


# TODO: Fix PDF Version of text extraction to find key words better
def extractPDF():

    pdfPath = os.path.join(
        FILEPATH,
        "phoenix_mobile_vending_and_mobile_food_vending_brochure.pdf",
    )

    try:
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
            pdfResults[category] = extractKeywords(pdfCleaned, terms)

        pdfJSON = {
            "file": os.path.basename(pdfPath),
            "keyword_contexts": pdfResults,
        }

        print(json.dumps(pdfJSON, indent=4))

        os.makedirs(SAVEPATH, exist_ok=True)
        saveFile = os.path.join(SAVEPATH, "pdf_analysis_output.json")
        with open(saveFile, "w", encoding="utf-8") as f:
            json.dump(pdfJSON, f, indent=2)

        print("[OK] PDF analysis file saved successfully")

    except Exception as e:
        print(f"[Error] An error occurred while processing {pdfPath}: {e}")


if __name__ == "__main__":
    extractTXT("Test document for legal stuff.txt")
    extractPDF("phoenix_mobile_vending_and_mobile_food_vending_brochure.pdf")

import os
import json
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
def extractPDF(filename):
    pdfPath = os.path.join(FILEPATH, filename)
    pdfRaw = accessDocuments(pdfPath)
    if not pdfRaw:
        exit()

    pdfCleaned = cleanText(pdfRaw)

    pdfResults = {}
    for category, terms in KEYWORDS.items():
        pdfResults[category] = extractKeywords(pdfCleaned, terms)

    pdfJSON = {
        "file": os.path.basename(filename),
        "cleaned_preview": pdfCleaned[:300] + "...",
        "keyword_contexts": pdfResults,
    }

    print(json.dumps(pdfJSON, indent=4))

    os.makedirs(SAVEPATH, exist_ok=True)
    saveFile = os.path.join(SAVEPATH, filename.replace(".pdf", ".json"))
    with open(saveFile, "w", encoding="utf-8") as saveFile:
        json.dump(pdfJSON, saveFile, indent=2)


if __name__ == "__main__":
    extractTXT("Test document for legal stuff.txt")
    extractPDF("phoenix_mobile_vending_and_mobile_food_vending_brochure.pdf")

import os, sys
from os.path import join, abspath, dirname, realpath
from os import makedirs, listdir
import json
from PyPDF2 import PdfReader
from Backend.Logic.mongo_db.extraction_collection import upsert_extraction
from Backend.Logic.extraction.extraction_util import cleanText, extractKeywords

# Define your keyword categories and terms
# Category: Terms []
KEYWORDS = {
  "webpage": [".gov", ".ca", "municipality", "city of", "regional district"],
  "checklist": ["checklist", "requirements list", "required documents"],
  "guide to license": ["guide", "how to apply", "licensing process", "application process"],
  "bylaws": ["bylaw", "regulation", "municipal code", "ordinance"],
  "penalties": ["fine", "fee", "penalty", "violation", "infraction"],
  "provincial business license": ["provincial business license", "provincial permit", "provincial approval", "provincial business name certificate"],
  "provincial food business license": ["provincial food business license", "food establishment permit", "provincial food vendor license"],
  "municipal business license": ["municipal business license", "local business permit", "city business license"],
  "municipal food business license": ["municipal food business license", "mobile food vendor license", "street food vendor license"],
  "retail license for CPG": ["consumer packaged good", "CPG", "retail goods", "branded retail products"],
  "curbside vending": ["curbside vending", "street vending", "mobile vending", "sidewalk vending"],
  "parking fees": ["parking fee", "metered parking", "vending zone", "designated vending area"],
  "noise bylaws": ["noise", "noise bylaw", "sound regulation", "amplified sound"],
  "traffic bylaws": ["traffic bylaw", "traffic regulation", "vehicle restriction", "road use", "traffic act"],
  "operation hours": ["operating hours", "business hours", "hours of operation", "time limit", "maximum duration", "hours at any one time"],
  "branded consumer goods": ["branding", "branded products", "product labeling", "consumer goods"],
  "private property operation": ["private property", "private lot", "owner permission", "property consent"],
  "proximity regulations": ["proximity regulation", "distance restriction", "buffer zone", "proximity limit"],
  "min distance to restaurant": ["distance to restaurant", "separation from restaurant", "nearby restaurant restriction", "from an open and operating restaurant"],
  "min distance to food truck": ["distance to other food trucks", "food truck spacing", "vendor proximity"],
  "non-food service proximity restrictions": ["proximity restriction", "non-food vendor proximity", "distance from other vendors"],
  "min distance proximity from other business": ["proximity to other business", "distance between vendors"],
  "num food trucks allowed in geographic area": ["number of food trucks allowed", "maximum food trucks per area", "vendor density limit", "food trucks per block"],
  "parking locations": ["designated parking", "allowed parking", "approved vending location", "vending area", "public road vending"],
  "additional private restrictions": ["private restrictions", "additional property rules", "landowner conditions"],
  "name of local authority": ["local authority", "licensing department", "municipal licensing office", "city clerk", "regulatory agency"],
  "direct link to authority": ["reach out", "contact", "reach", "office", "call", "email", "phone"],
  "insurance requirements": ["insurance", "liability coverage", "certificate of insurance", "proof of insurance"],
  "physical requirements for trucks": ["vehicle requirements", "truck must have", "equipment standards", "vehicle condition", "inspection requirements", "plate number", "license number", "business name", "client's name"],
  "exterior appearance guidelines": ["paint", "painted", "appearance", "vehicle signage", "branding on truck", "exterior look", "color", "color contrast", "colour", "colour contrast", "identification markings"]
}

FILEPATH = abspath(join(dirname( __file__ ),"..", "..", "test documents"))
# TODO: replace with MongoDB code
SAVEPATH = abspath(join(dirname( __file__ ),"..", "..", "analysis_ready"))


def extractTXT(filename):
    txtPath = join(FILEPATH, filename)
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

    upsert_extraction(txtJSON)

    # makedirs(SAVEPATH, exist_ok=True)
    # saveFile = join(SAVEPATH, filename.replace(".txt", ".json"))
    # with open(saveFile, "w", encoding="utf-8") as saveFile:
        # json.dump(txtJSON, saveFile, indent=2)

    print("Extracted txt file")


def extractPDF(filename):
    pdfPath = join(FILEPATH, filename)

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
        "file": filename,
        "keyword_contexts": pdfResults,
    }

    upsert_extraction(pdfJSON)

    # makedirs(SAVEPATH, exist_ok=True)
    # saveFile = join(SAVEPATH, filename.replace(".pdf", ".json"))
    # with open(saveFile, "w", encoding="utf-8") as saveFile:
        # json.dump(pdfJSON, saveFile, indent=2)

    print("Extracted pdf file")


def extract():
    print(dirname(realpath(__file__)))
    print(FILEPATH)
    for file_name in listdir(FILEPATH):
        if file_name.lower().endswith(".txt"):
            extractTXT(file_name)
        elif file_name.lower().endswith(".pdf"):
            extractPDF(file_name)

if __name__ == "__main__":
    extract()
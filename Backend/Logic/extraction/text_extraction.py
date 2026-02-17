from os.path import join, abspath, dirname, realpath
from os import listdir
from PyPDF2 import PdfReader
from Backend.Logic.mongo_db.extraction_collection import upsertExtraction
from Backend.Logic.extraction.extraction_util import cleanText, extractKeywords
import spacy
import re

nlp = spacy.load("en_core_web_sm")

# Define your keyword categories and terms
# Category: Terms []
KEYWORDS = {
    "webpage": [".gov", ".ca", "municipality", "city of", "regional district"],
    "checklist": ["checklist", "requirements list", "required documents"],
    "guide to license": ["guide", "how to apply", "licensing process", "application process"],
    "bylaws": ["bylaw", "regulation", "municipal code", "ordinance"],
    "penalties": ["fine", "fee", "penalty", "violation", "infraction"],
    "provincial business license": ["provincial business license", "provincial permit", "provincial approval",
                                    "provincial business name certificate"],
    "provincial food business license": ["provincial food business license", "food establishment permit",
                                         "provincial food vendor license"],
    "municipal business license": ["municipal business license", "local business permit", "city business license"],
    "municipal food business license": ["municipal food business license", "mobile food vendor license",
                                        "street food vendor license"],
    "retail license for CPG": ["consumer packaged good", "CPG", "retail goods", "branded retail products"],
    "curbside vending": ["curbside vending", "street vending", "mobile vending", "sidewalk vending"],
    "parking fees": ["parking fee", "metered parking", "vending zone", "designated vending area"],
    "noise bylaws": ["noise", "noise bylaw", "sound regulation", "amplified sound"],
    "traffic bylaws": ["traffic bylaw", "traffic regulation", "vehicle restriction", "road use", "traffic act"],
    "operation hours": ["operating hours", "business hours", "hours of operation", "time limit", "maximum duration",
                        "hours at any one time"],
    "branded consumer goods": ["branding", "branded products", "product labeling", "consumer goods"],
    "private property operation": ["private property", "private lot", "owner permission", "property consent"],
    "proximity regulations": ["proximity regulation", "distance restriction", "buffer zone", "proximity limit"],
    "min distance to restaurant": ["distance to restaurant", "separation from restaurant",
                                   "nearby restaurant restriction", "from an open and operating restaurant"],
    "min distance to food truck": ["distance to other food trucks", "food truck spacing", "vendor proximity"],
    "non-food service proximity restrictions": ["proximity restriction", "non-food vendor proximity",
                                                "distance from other vendors"],
    "min distance proximity from other business": ["proximity to other business", "distance between vendors"],
    "num food trucks allowed in geographic area": ["number of food trucks allowed", "maximum food trucks per area",
                                                   "vendor density limit", "food trucks per block"],
    "parking locations": ["designated parking", "allowed parking", "approved vending location", "vending area",
                          "public road vending"],
    "additional private restrictions": ["private restrictions", "additional property rules", "landowner conditions"],
    "name of local authority": ["local authority", "licensing department", "municipal licensing office", "city clerk",
                                "regulatory agency"],
    "direct link to authority": ["reach out", "contact", "reach", "office", "call", "email", "phone"],
    "insurance requirements": ["insurance", "liability coverage", "certificate of insurance", "proof of insurance"],
    "physical requirements for trucks": ["vehicle requirements", "truck must have", "equipment standards",
                                         "vehicle condition", "inspection requirements", "plate number",
                                         "license number", "business name", "client's name"],
    "exterior appearance guidelines": ["paint", "painted", "appearance", "vehicle signage", "branding on truck",
                                       "exterior look", "color", "color contrast", "colour", "colour contrast",
                                       "identification markings"]
}


def split_sentences(text):
    doc = nlp(text)
    return [sent for sent in doc.sents if sent.text.strip()]


# TODO: Change to where files need to be stored
FILEPATH = abspath(join(dirname(__file__), "..", "..", "test_documents"))

DISTANCE_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:linear|horizontal|vertical|approx(?:\.|imately)?|about)?\s*'
    r'(m|meter|meters|metre|metres|km|kilometer|kilometers|kilometre|kilometres)\b',
    re.IGNORECASE)

DISTANCE_WORDS = {"within": "within",
                  "no closer than": "minimum",
                  "at least": "minimum",
                  "no less than": "minimum",
                  "from": "from",
                  "of": "of"}


# TODO: Add all other RE layers for the other categories and extractions.

def extract_distance(sentence):
    matches = DISTANCE_RE.findall(sentence)
    if not matches:
        return None
    values = []
    for value, unit in matches:
        values.append({"value": float(value), "unit": unit.lower()})
    return values


DISTANCE_WEIGHTS = {"shall": 0.2, "must": 0.2, "shall not": 0.3,
                    "must not": 0.3, "within": 0.2, "no closer than": 0.3,
                    "at least": 0.2, "minimum": 0.2, "distance": 0.2,
                    "restricted": 0.3, "prohibited": 0.3, "cannot": 0.2}


def distance_context_score(text):
    score = 0.0
    lower = text.lower()
    for keyword, weight in DISTANCE_WEIGHTS.items():
        if keyword in lower:
            score += weight
    return min(score, 1.0)


def distance_modality(sentence):
    modals = {"shall", "must", "may"}
    for word in sentence:
        if word.text.lower() in modals:
            return 0.2
    return 0.0


def distance_negation(sentence):
    negations = {"except", "unless", "not applicable"}
    for word in sentence:
        if word.text.lower() in negations:
            return -0.3
    return 0.0


def distance_confidence(sentence):
    score = 0.4
    score += distance_context_score(sentence.text)
    score += distance_modality(sentence)
    score += distance_negation(sentence)
    return round(max(0, 0, min(score, 1.0)), 2)


def distance_criteria(sentence):
    distances = extract_distance(sentence.text)
    if not distances:
        return None
    text = sentence.text.lower()

    if "shall not" in text or "must not" in text:
        meaning = "prohibited"
    elif "shall" in text or "must" in text:
        meaning = "required"
    else:
        meaning = "unknown"

    relations = None
    for key in ["within", "from", "of", "no closer than", "at least"]:
        if key in text:
            relations = key
            break

    subject = None
    for token in sentence:
        if token.dep_ in ("nsubj", "nsubjpass"):
            subject = token.text
            break

    action = None
    for token in sentence:
        if token.pos_ == "VERB":
            action = token.lemma_
            break

    confidence = distance_confidence(sentence)

    return {
        "criteria": "distance_restriction",
        "distances": distances,
        "relations": relations,
        "subject": subject,
        "action": action,
        "meaning": meaning,
        "confidence": confidence,
        "source": sentence.text
    }


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
    sentences = split_sentences(txtCleaned)
    txtResults = {}

    for category, terms in KEYWORDS.items():
        matches = []
        for sentence in sentences:
            hits = extractKeywords(sentence.text, terms)
            if hits:
                re_data = {}
                if category in ["min distance to restaurant", "min distance to food truck", "proximity regulations",
                                "non-food service proximity restrictions",
                                "min distance proximity from other business"]:
                    distance_rule = distance_criteria(sentence)
                    if distance_rule:
                        re_data["distance_criteria"] = distance_rule
                entry = {"sentence": sentence.text, "hits": hits}
                if re_data:
                    entry["regex"] = re_data
                matches.append(entry)
        if matches:
            txtResults[category] = matches

    txtJSON = {
        "file": filename,
        "keyword_contexts": txtResults,
    }

    upsertExtraction(txtJSON)
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
    sentences = split_sentences(pdfCleaned)
    pdfResults = {}

    for category, terms in KEYWORDS.items():
        matches = []
        for sentence in sentences:
            hits = extractKeywords(sentence.text, terms)
            if hits:
                re_data = {}
                if category in ["min distance to restaurant", "min distance to food truck", "proximity regulations",
                                "non-food service proximity restrictions",
                                "min distance proximity from other business"]:
                    distance_rule = distance_criteria(sentence)
                    if distance_rule:
                        re_data["distance_criteria"] = distance_rule
                entry = {"sentence": sentence.text, "hits": hits}
                if re_data:
                    entry["regex"] = re_data
                matches.append(entry)
        if matches:
            pdfResults[category] = matches

    pdfJSON = {
        "file": filename,
        "keyword_contexts": pdfResults,
    }

    upsertExtraction(pdfJSON)
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

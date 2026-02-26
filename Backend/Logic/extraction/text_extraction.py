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
    "webpage": [".gov", ".ca", "municipality", "city of", "regional district"],  # covered
    "checklist": ["checklist", "requirements list", "required documents"],
    "guide to license": ["guide", "how to apply", "licensing process", "application process"],  # covered
    "bylaws": ["bylaw", "regulation", "municipal code", "ordinance"],
    "penalties": ["fine", "fee", "penalty", "violation", "infraction"],
    "provincial business license": ["provincial business license", "provincial permit", "provincial approval",
                                    # covered
                                    "provincial business name certificate"],
    "provincial food business license": ["provincial food business license", "food establishment permit",  # covered
                                         "provincial food vendor license"],
    "municipal business license": ["municipal business license", "local business permit", "city business license"],
    # covered
    "municipal food business license": ["municipal food business license", "mobile food vendor license",  # covered
                                        "street food vendor license"],
    "retail license for CPG": ["consumer packaged good", "CPG", "retail goods", "branded retail products"],  # covered
    "curbside vending": ["curbside vending", "street vending", "mobile vending", "sidewalk vending"],
    "parking fees": ["parking fee", "metered parking", "vending zone", "designated vending area"],
    "noise bylaws": ["noise", "noise bylaw", "sound regulation", "amplified sound"],
    "traffic bylaws": ["traffic bylaw", "traffic regulation", "vehicle restriction", "road use", "traffic act"],
    "operation hours": ["operating hours", "business hours", "hours of operation", "time limit", "maximum duration",
                        "hours at any one time"],
    "branded consumer goods": ["branding", "branded products", "product labeling", "consumer goods"],
    "private property operation": ["private property", "private lot", "owner permission", "property consent"],
    "proximity regulations": ["proximity regulation", "distance restriction", "buffer zone", "proximity limit"],
    # covered
    "min distance to restaurant": ["distance to restaurant", "separation from restaurant",  # covered
                                   "nearby restaurant restriction", "from an open and operating restaurant"],
    "min distance to food truck": ["distance to other food trucks", "food truck spacing", "vendor proximity"],
    # covered
    "non-food service proximity restrictions": ["proximity restriction", "non-food vendor proximity",  # covered
                                                "distance from other vendors"],
    "min distance proximity from other business": ["proximity to other business", "distance between vendors"],
    # covered
    "num food trucks allowed in geographic area": ["number of food trucks allowed", "maximum food trucks per area",
                                                   "vendor density limit", "food trucks per block"],
    "parking locations": ["designated parking", "allowed parking", "approved vending location", "vending area",
                          "public road vending"],
    "additional private restrictions": ["private restrictions", "additional property rules", "landowner conditions"],
    "name of local authority": ["local authority", "licensing department", "municipal licensing office", "city clerk",
                                "regulatory agency"],  # covered
    "direct link to authority": ["reach out", "contact", "reach", "office", "call", "email", "phone"],  # covered
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
LICENSE_RE = re.compile(
    r'(provincial|municipal|city|local)?\s*'
    r'(business|food)?\s*'
    r'(license|licence|permit|approval|certificate)',
    re.IGNORECASE)
WEBPAGE_RE = re.compile(
    r'https?://[^\s)"]+|'
    r'\b[\w\-]+\.(?:gov|gov\.ca|ca)\b|'
    r'\b(city of|municipality of|regional district of)\s+[A-Z][a-zA-Z\s]+',
    re.IGNORECASE)
AUTHORITY_NAME_RE = re.compile(
    r'local authority|'
    r'licensing department|'
    r'municipal licensing office|'
    r'city clerk|'
    r'regulatory agency|'
    r'department of [A-Za-z\s]+|'
    r'[A-Z][a-zA-Z\s]+ (Department|Office|Authority|Division)',
    re.IGNORECASE)
AUTHORITY_CONTACT_RE = re.compile(
    r'\b(contact|reach out to|reach|call|email|phone)\b|'
    r'\bfor more information\b|'
    r'\bvisit\b.*\bwebsite\b|'
    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|'
    r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    re.IGNORECASE)

LICENSE_WORDS = {
    "provincial_business": [
        "provincial business license",
        "provincial business licence",
        "provincial permit",
        "provincial approval",
        "business name certificate"
    ],
    "provincial_food": [
        "provincial food business license",
        "provincial food business licence",
        "food establishment permit",
        "food vendor license",
        "food vendor licence"
    ],
    "municipal_business": [
        "municipal business license",
        "municipal business licence",
        "city business license",
        "city business licence",
        "local business permit"
    ],
    "municipal_food": [
        "municipal food business license",
        "municipal food business licence",
        "mobile food vendor license",
        "mobile food vendor licence",
        "street food vendor license",
        "street food vendor licence"
    ]
}

AUTHORITY_WORDS = {
    "authority_name": [
        "local authority",
        "licensing department",
        "municipal licensing office",
        "city clerk",
        "regulatory agency",
        "department",
        "office",
        "authority",
        "division"
    ],
    "authority_contact": [
        "contact",
        "reach out",
        "call",
        "email",
        "phone",
        "for more information",
        "inquiries"
    ],
    "authority_web": [
        "website",
        "webpage",
        ".gov",
        ".ca",
        "online"
    ]
}


# TODO: Add all other RE layers for the other categories and extractions.
def extract_authority(sentence):
    text = sentence.lower()
    found = []
    for authority_type, phrases in AUTHORITY_WORDS.items():
        for phrase in phrases:
            if phrase in text:
                found.append(authority_type)
                break
    if found:
        return list(set(found))
    else:
        return None


def extract_license(sentence):
    text = sentence.lower()
    found = []
    for license_type, phrases in LICENSE_WORDS.items():
        for phrase in phrases:
            if phrase in text:
                found.append(license_type)
                break
    if not found and LICENSE_RE.search(text):
        found.append("other_license")
    if found:
        return list(set(found))
    else:
        return None


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
LICENSE_WEIGHTS = {"shall": 0.3, "must": 0.3, "required": 0.3, "mandatory": 0.3,
                   "condition of approval": 0.2, "prior to operating": 0.2,
                   "before operating": 0.2, "required to obtain": 0.3}
AUTHORITY_WEIGHTS = {"contact": 0.2, "reach out": 0.2, "licensing department": 0.3,
                     "city clerk": 0.3, "website": 0.2, ".gov": 0.3,
                     "email": 0.2, "phone": 0.2, "calling": 0.2, "line": 0.2}


def authority_context_score(text):
    score = 0.0
    lower = text.lower()
    for keyword, weight in AUTHORITY_WEIGHTS.items():
        if keyword in lower:
            score += weight
    return min(score, 1.0)


def license_context_score(text):
    score = 0.0
    lower = text.lower()
    for keyword, weight in LICENSE_WEIGHTS.items():
        if keyword in lower:
            score += weight
    return min(score, 1.0)


def distance_context_score(text):
    score = 0.0
    lower = text.lower()
    for keyword, weight in DISTANCE_WEIGHTS.items():
        if keyword in lower:
            score += weight
    return min(score, 1.0)


def modality(sentence):
    modals = {"shall", "must", "may"}
    for word in sentence:
        if word.text.lower() in modals:
            return 0.2
    return 0.0


def negation(sentence):
    negations = {"except", "unless", "not applicable", "not required", "exempt", "exemption", "does not require"}
    lower = sentence.text.lower()
    for negation in negations:
        if negation in lower:
            return -0.3
    return 0.0


def authority_confidence(sentence):
    score = 0.4
    score += authority_context_score(sentence.text)
    score += modality(sentence)
    score += negation(sentence)
    return round(max(0, min(score, 1.0)), 2)


def license_confidence(sentence):
    score = 0.4
    score += license_context_score(sentence.text)
    score += modality(sentence)
    score += negation(sentence)
    return round(max(0, min(score, 1.0)), 2)


def distance_confidence(sentence):
    score = 0.4
    score += distance_context_score(sentence.text)
    score += modality(sentence)
    score += negation(sentence)
    return round(max(0, min(score, 1.0)), 2)


def authority_criteria(sentence):
    authority = extract_authority(sentence.text)
    if not authority:
        return None
    text = sentence.text.lower()

    if (".gov" in text or ".ca" in text) and "@" not in text:
        meaning = "link"
    elif "@" in text or "email" in text:
        meaning = "email address"
    elif "local" in text or "department" in text or "office" in text:
        meaning = "government"
    elif re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", text):
        meaning = "phone number"
    else:
        meaning = "unknown"

    confidence = authority_confidence(sentence)

    return {
        "criteria": "authority_contact",
        "authority_type": authority,
        "meaning": meaning,
        "confidence": confidence,
        "source": sentence.text
    }


def license_criteria(sentence):
    licenses = extract_license(sentence.text)
    if not licenses:
        return None
    text = sentence.text.lower()

    if "shall not" in text or "must not" in text or "not required" in text:
        meaning = "not_required"
    elif "shall" in text or "must" in text or "required" in text:
        meaning = "required"
    elif "may" in text:
        meaning = "optional"
    else:
        meaning = "unknown"

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

    confidence = license_confidence(sentence)

    return {
        "criteria": "license_requirement",
        "license_types": licenses,
        "meaning": meaning,
        "subject": subject,
        "action": action,
        "confidence": confidence,
        "source": sentence.text
    }


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
                if category in ["webpage", "direct link to authority", "name of local authority"]:
                    authority_rule = authority_criteria(sentence)
                    if authority_rule:
                        re_data["authority_criteria"] = authority_rule
                if category in ["provincial business license", "provincial food business license",
                                "municipal business license", "municipal food business license",
                                "retail license for CPG"]:
                    license_rule = license_criteria(sentence)
                    if license_rule:
                        re_data["license_criteria"] = license_rule
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
                if category in ["webpage", "direct link to authority", "name of local authority"]:
                    authority_rule = authority_criteria(sentence)
                    if authority_rule:
                        re_data["authority_criteria"] = authority_rule
                if category in ["provincial business license", "provincial food business license",
                                "municipal business license", "municipal food business license",
                                "retail license for CPG"]:
                    license_rule = license_criteria(sentence)
                    if license_rule:
                        re_data["license_criteria"] = license_rule
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

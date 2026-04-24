"""
Text Extraction Module

This module processes documents (TXT, PDF, and URLs) to extract structured
information based on predefined keyword categories and regex-based criteria.

Main Responsibilities:
- Load and clean document text
- Split text into sentences
- Match sentences against keyword categories
- Apply rule-based extraction (regex + NLP helpers)
- Store extracted results into MongoDB

Dependencies:
- BeautifulSoup (HTML parsing)
- PyPDF2 (PDF parsing)
- Custom utilities (cleanText, extractKeywords, etc.)
"""

from os.path import join, abspath, dirname, realpath
from os import listdir
import re
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from Backend.Logic.mongo_db.extraction_collection import upsertExtraction
from Backend.Logic.extraction.extraction_util import cleanText, extractKeywords, splitSentences, computeConfidence, extractMeaning


# KEYWORD DEFINITIONS

# Dictionary mapping category names to keyword lists.
# These keywords are used to identify relevant sentences.
KEYWORDS = {
    # Core regulatory categories
    "fire safety core": ["fire code", "propane", "suppression", "sprinkler", "extinguisher", "flammable", "hazard"],
    "food safety core": ["food safety", "public health", "sanitation", "temperature", "haccp", "health officer"],
    "zoning core": ["zoning", "zone", "land use", "site plan", "occupancy", "setback", "district"],
    "legal structure": ["section", "enforcement", "compliance", "ammend", "repeal", "supersede"],

    # Web and document structure
    "webpage": [".gov", ".ca", "municipality", "city of", "regional district"],
    "checklist": ["checklist", "requirements list", "required documents"],
    "guide to license": ["guide", "how to apply", "licensing process", "application process"],
    "bylaws": ["bylaw", "regulation", "municipal code", "ordinance"],

    # Financial / penalties
    "penalties": ["fine", "fee", "penalty", "violation", "infraction"],

    # Licensing categories
    "provincial business license": ["provincial business license", "provincial permit", "provincial approval",
                                    "provincial business name certificate"],
    "provincial food business license": ["provincial food business license", "food establishment permit",
                                         "provincial food vendor license"],
    "municipal business license": ["municipal business license", "local business permit", "city business license"],
    "municipal food business license": ["municipal food business license", "mobile food vendor license",
                                        "street food vendor license"],

    # Operational constraints
    "retail license for CPG": ["consumer packaged good", "CPG", "retail goods", "branded retail products"],
    "curbside vending": ["curbside vending", "street vending", "mobile vending", "sidewalk vending"],
    "parking fees": ["parking fee", "metered parking", "vending zone", "designated vending area"],
    "noise bylaws": ["noise", "noise bylaw", "sound regulation", "amplified sound"],
    "traffic bylaws": ["traffic bylaw", "traffic regulation", "vehicle restriction", "road use", "traffic act"],
    "operation hours": ["operating hours", "business hours", "hours of operation", "time limit", "maximum duration",
                        "hours at any one time"],

    # Physical + business rules
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

    # Authority and compliance
    "additional private restrictions": ["private restrictions", "additional property rules", "landowner conditions"],
    "name of local authority": ["local authority", "licensing department", "municipal licensing office", "city clerk",
                                "regulatory agency"],
    "direct link to authority": ["reach out", "contact", "reach", "office", "call", "email", "phone"],

    # Requirements
    "insurance requirements": ["insurance", "liability coverage", "certificate of insurance", "proof of insurance"],
    "physical requirements for trucks": ["vehicle requirements", "truck must have", "equipment standards",
                                         "vehicle condition", "inspection requirements", "plate number",
                                         "license number", "business name", "client's name"],
    "exterior appearance guidelines": ["paint", "painted", "appearance", "vehicle signage", "branding on truck",
                                       "exterior look", "color", "color contrast", "colour", "colour contrast",
                                       "identification markings"]
}


# FILE CONFIGURATION

# Base directory for test documents
FILEPATH = abspath(join(dirname(__file__), "..", "..", "test_documents"))


# REGEX PATTERNS

# Regex patterns used to detect structured information
DISTANCE_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:linear|horizontal|vertical|approx(?:\.|imately)?|about)?\s*'
    r'(m|meter|meters|metre|metres|km|kilometer|kilometers|kilometre|kilometres)\b',
    re.IGNORECASE)

LICENSE_RE = re.compile(
    r'(provincial|municipal|city|local)?\s*'
    r'(business|food)?\s*'
    r'(license|licence|permit|approval|certificate)',
    re.IGNORECASE)


# EXTRACTION HELPER FUNCTIONS

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
TIME_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(hour|hours|hr|hrs|minute|minutes)\b',
    re.IGNORECASE)
CURRENCY_RE = re.compile(
    r'\$\s?\d+(?:,\d{3})*(?:\.d{2})?',
    re.IGNORECASE)
CURBSIDE_RE = re.compile(
    r'\b(curbside|street|sidewalk|roadside)\b.*\b(vend|vendor|vending|operate)\b|'
    r'\b(mobile|food truck|vehicle)\b.*\b(curbstone|curb)\b',
    re.IGNORECASE)
PARKING_FEE_RE = re.compile(
    r'\b(parking|metered|pay station|parking meter)\b.*\$\s?\d+|'
    r'\$\s?\d+.*\b(parking|metered)\b',
    re.IGNORECASE)
TRAFFIC_RE = re.compile(
    r'\b(traffic|roadway|highway|intersection|lane)\b.*\b(restrict|prohibit|regulate|permit)\b|'
    r'\b(traffic act|motor vehicle act|highway traffic)\b',
    re.IGNORECASE)
PARKING_LOCATION_RE = re.compile(
    r'\b(designated|approved|authorized)\b.*\b(parking|vending area|zone)\b|'
    r'\b(public street|public road|municipal roadway)\b',
    re.IGNORECASE)
PRIVATE_PROPERTY_RE = re.compile(
    r'\b(private property|private lot|privately owned)\b|'
    r'\b(owner consent|written permission|landowner approval)\b',
    re.IGNORECASE)
PRIVATE_RESTRICTION_RE = re.compile(
    r'\b(in addition to|subject to|at the discretion of)\b.*\b(property owner|landowner)\b|'
    r'\b(private restrictions|additional conditions)\b',
    re.IGNORECASE)
PHYSICAL_TRUCK_RE = re.compile(
    r'\b(vehicle|truck|mobile unit|food truck)\b.*'
    r'\b(must|shall|required|equipped|maintained|inspected|contain|have)\b|'
    r'\b(fire suppression|hand[-\s]?wash sink|refrigeration|generator|propane|electrical system)\b|'
    r'\b(vin|vehicle identification number|plate number|license plate|business name)\b|'
    r'\b(mechanical condition|safe operating condition|roadworthy)\b',
    re.IGNORECASE)
EXTERIOR_APPEARANCE_RE = re.compile(
    r'\b(exterior|appearance|visible|displayed|clearly visible)\b.*'
    r'\b(must|shall|required|maintained)\b|'
    r'\b(signage|sign|logo|branding|business name)\b|'
    r'\b(color|colour|colors|colours|contrast|legible|readable)\b|'
    r'\b(no graffiti|clean condition|free of damage|painted|paint)\b',
    re.IGNORECASE)
MEASUREMENT_RE = re.compile(
    r'(?P<value>\d+(?:\.\d+)?)\s*'
    r'(?P<unit>inches?|inch|in\.?|cm|mm|millimeters?|millimetres?)\b',
    re.IGNORECASE)
BYLAW_RE = re.compile(
    r'\b(by[- ]?law|ordinance|municipal code|city code|chapter\s+\d+|section\s+\d+)\b', re.IGNORECASE)
LICENSE_GUIDE_RE = re.compile(
    r'\b(how to apply|application process|licensing process|step\s*\d+|follow these steps|apply for a license)\b',
    re.IGNORECASE)
CHECKLIST_RE = re.compile(
    r'(\[\s?\]|\☐|\✔|\•|-)\s+|'
    r'\b(checklist|required documents|documents required|application checklist)\b',
    re.IGNORECASE)

MEASUREMENT_WORDS = {
    "height": [
        "height",
        "high",
        "tall"
    ],
    "width": [
        "width",
        "wide"
    ],
    "length": [
        "length",
        "long"
    ],
    "lettering_height": [
        "letter",
        "lettering",
        "font",
        "text"
    ],
    "plate_number": [
        "plate number",
        "license plate",
        "registration number"
    ],
    "signage": [
        "sign",
        "signage",
        "display",
        "business name"
    ]
}

OPERATIONAL_WORDS = {
    "hours": [
        "operating hours",
        "business hours",
        "hours of operation",
        "time limit",
        "maximum duration"
    ],
    "noise": [
        "noise",
        "sound",
        "amplified sound",
        "noise bylaw"
    ],
    "insurance": [
        "insurance",
        "liability coverage",
        "certificate of insurance",
        "proof of insurance"
    ],
    "penalty": [
        "fine",
        "penalty",
        "violation",
        "infraction",
        "fee"
    ],
    "branding": [
        "branding",
        "product labeling",
        "branded products",
        "consumer goods"
    ]
}

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


def extract_physical_measurements(sentence):
    """
    Extracts physical measurement values (e.g., height, width) from a sentence.

    Args:
        sentence: NLP sentence object

    Returns:
        List of measurement dictionaries or None
    """
    text = sentence.text.lower()
    matches = MEASUREMENT_RE.findall(sentence.text)
    if not matches:
        return None

    found = []
    for value, unit in matches:
        attribute = None

        # Determine measurement type (height, width, etc.)
        for attr, keywords in MEASUREMENT_WORDS.items():
            for keyword in keywords:
                if keyword in text:
                    attribute = attr
                    break
            if attribute:
                break

        found.append({
            "value": float(value),
            "unit": unit.lower(),
            "attribute": attribute or "unspecified"
        })

    return found if found else None


def extract_operational(sentence):
    """
    Identifies operational-related keywords (e.g., hours, noise, insurance).

    Args:
        sentence (str): sentence text

    Returns:
        List of operational categories or None
    """
    text = sentence.lower()
    found = []

    for operational_type, phrases in OPERATIONAL_WORDS.items():
        for phrase in phrases:
            if phrase in text:
                found.append(operational_type)
                break

    return list(set(found)) if found else None


def extract_authority(sentence):
    """
    Extracts authority-related references (e.g., department, contact info).

    Args:
        sentence (str)

    Returns:
        List of authority types or None
    """
    text = sentence.lower()
    found = []

    for authority_type, phrases in AUTHORITY_WORDS.items():
        for phrase in phrases:
            if phrase in text:
                found.append(authority_type)
                break

    return list(set(found)) if found else None


def extract_license(sentence):
    """
    Detects license-related phrases and categorizes them.

    Args:
        sentence (str)

    Returns:
        List of license types or None
    """
    text = sentence.lower()
    found = []

    for license_type, phrases in LICENSE_WORDS.items():
        for phrase in phrases:
            if phrase in text:
                found.append(license_type)
                break

    if not found and LICENSE_RE.search(text):
        found.append("other_license")

    return list(set(found)) if found else None


def extract_distance(sentence):
    """
    Extracts distance values from text.

    Args:
        sentence (str)

    Returns:
        List of distance dictionaries or None
    """
    matches = DISTANCE_RE.findall(sentence)
    if not matches:
        return None

    return [{"value": float(value), "unit": unit.lower()} for value, unit in matches]


# CRITERIA FUNCTIONS

# Each function evaluates a sentence for a specific rule type
# and returns structured extraction results if matched.
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
OPERATIONAL_WEIGHTS = {"shall": 0.3, "must": 0.2, "shall not": 0.3,
                       "must not": 0.3, "prohibited": 0.3, "operating hours": 0.3,
                       "hours of operation": 0.3, "time limit": 0.3, "noise": 0.3,
                       "amplified sound": 0.3, "sound regulation": 0.3, "insurance": 0.3,
                       "liability coverage": 0.3, "certificate of insurance": 0.3, "fine": 0.3,
                       "penalty": 0.3, "violation": 0.3, "infraction": 0.3,
                       "may": 0.1, "permitted": 0.1}
CHECKLIST_WEIGHTS = {"checklist": 0.4, "required documents": 0.3, "application checklist": 0.4,
                     "must include": 0.2, "submit": 0.2, "provide": 0.2}
GUIDE_WEIGHTS = {"how to apply": 0.4, "application process": 0.3, "licensing process": 0.3,
                 "step": 0.3, "follow these steps": 0.4, "apply for": 0.2}
BYLAW_WEIGHTS = {"bylaw": 0.4, "ordinance": 0.4, "municipal code": 0.4,
                 "chapter": 0.2, "section": 0.2}


def checklist_criteria(sentence):
    """Extracts checklist-style requirements from a sentence."""
    if not CHECKLIST_RE.search(sentence.text):
        return None

    documents = re.findall(
        r'(proof of insurance|application form|permit|certificate|identification)',
        sentence.text,
        re.IGNORECASE)

    return {
        "criteria": "license_checklist",
        "documents": documents if documents else None,
        "confidence": computeConfidence(sentence, CHECKLIST_WEIGHTS),
        "source": sentence.text
    }


# RULE DISPATCH

"""
Maps keyword categories to their corresponding extraction functions.
This allows dynamic routing of sentence processing.
"""
def license_guide_criteria(sentence):
    if not LICENSE_GUIDE_RE.search(sentence.text):
        return None

    steps = re.findall(r'step\s*\d+', sentence.text, re.IGNORECASE)

    return {
        "criteria": "license_guide",
        "steps_detected": steps if steps else None,
        "confidence": computeConfidence(sentence, GUIDE_WEIGHTS),
        "source": sentence.text
    }


def bylaw_criteria(sentence):
    if not BYLAW_RE.search(sentence.text):
        return None

    return {
        "criteria": "bylaw_reference",
        "confidence": computeConfidence(sentence, BYLAW_WEIGHTS),
        "source": sentence.text
    }


def exterior_appearance_criteria(sentence):
    if not EXTERIOR_APPEARANCE_RE.search(sentence.text):
        return None
    text = sentence.text.lower()

    meaning = extractMeaning(text)

    attributes = []
    for keyword in ["signage", "business name", "logo", "branding", "color", "colour", "contrast", "legible",
                    "visible", "clean", "sign", "signs", "logos", "colors", "colours"]:
        if keyword in text:
            attributes.append(keyword)

    return {
        "criteria": "exterior_appearance_guideline",
        "meaning": meaning,
        "attributes": attributes if attributes else None,
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def physical_truck_criteria(sentence):
    if not PHYSICAL_TRUCK_RE.search(sentence.text):
        return None
    text = sentence.text.lower()

    meaning = extractMeaning(text)

    equipment = []
    for keyword in ["fire suppression", "sink", "refrigeration", "generator", "propane", "electrical", "vin",
                    "plate number", "license plate", "licence plate", "business name"]:
        if keyword in text:
            equipment.append(keyword)

    measurements = extract_physical_measurements(sentence)

    return {
        "criteria": "physical_truck_requirement",
        "meaning": meaning,
        "measurements": measurements,
        "equipment": equipment if equipment else None,
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def traffic_criteria(sentence):
    if not TRAFFIC_RE.search(sentence.text):
        return None
    text = sentence.text.lower()

    meaning = extractMeaning(text)

    return {
        "criteria": "traffic_bylaw",
        "meaning": meaning,
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def private_property_criteria(sentence):
    if not (PRIVATE_PROPERTY_RE.search(sentence.text) or PRIVATE_RESTRICTION_RE.search(sentence.text)):
        return None
    text = sentence.text.lower()

    meaning = extractMeaning(text)

    return {
        "criteria": "private_property_operation",
        "meaning": meaning,
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def parking_location_criteria(sentence):
    if not PARKING_LOCATION_RE.search(sentence.text):
        return None

    return {
        "criteria": "parking_location",
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def parking_fee_criteria(sentence):
    if not PARKING_FEE_RE.search(sentence.text):
        return None
    fees = CURRENCY_RE.findall(sentence.text)

    return {
        "criteria": "parking_fee",
        "fees": fees if fees else None,
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def curbside_criteria(sentence):
    if not CURBSIDE_RE.search(sentence.text):
        return None
    text = sentence.text.lower()

    meaning = extractMeaning(text)

    return {
        "criteria": "curbside_vending",
        "meaning": meaning,
        "confidence": computeConfidence(sentence, OPERATIONAL_WEIGHTS),
        "source": sentence.text
    }


def operational_criteria(sentence):
    operational = extract_operational(sentence.text)
    if not operational:
        return None
    text = sentence.text.lower()

    meaning = extractMeaning(text)

    confidence = computeConfidence(sentence, OPERATIONAL_WEIGHTS)

    times = TIME_RE.findall(sentence.text)
    fines = CURRENCY_RE.findall(sentence.text)

    if times or fines:
        confidence += 0.2
        confidence = round(max(0, min(confidence, 1.0)), 2)

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

    return {
        "criteria": "operational_rule",
        "operational_types": operational,
        "meaning": meaning,
        "subject": subject,
        "action": action,
        "time_constraints": times if times else None,
        "financial_penalties": fines if fines else None,
        "confidence": confidence,
        "source": sentence.text
    }


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

    confidence = computeConfidence(sentence, AUTHORITY_WEIGHTS)

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

    meaning = extractMeaning(text)

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

    confidence = computeConfidence(sentence, LICENSE_WEIGHTS)

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

    meaning = extractMeaning(text)

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

    confidence = computeConfidence(sentence, DISTANCE_WEIGHTS)

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


RULE_DISPATCH = {
    "checklist": ("checklist_criteria", checklist_criteria),
    "guide to license": ("guide_to_license_criteria", license_guide_criteria),
    "bylaws": ("bylaw_criteria", bylaw_criteria),
    "physical requirements for trucks": ("physical_requirements_criteria", physical_truck_criteria),
    "exterior appearance guidelines": ("appearance_criteria", exterior_appearance_criteria),
    "private property operation": ("private_criteria", private_property_criteria),
    "additional private restrictions": ("private_criteria", private_property_criteria),
    "traffic bylaws": ("traffic_criteria", traffic_criteria),
    "parking locations": ("parking_locations_criteria", parking_location_criteria),
    "parking fees": ("parking_fees_criteria", parking_fee_criteria),
    "curbside vending": ("curbside_criteria", curbside_criteria),

    "penalties": ("operational_criteria", operational_criteria),
    "noise bylaws": ("operational_criteria", operational_criteria),
    "operation hours": ("operational_criteria", operational_criteria),
    "insurance requirements": ("operational_criteria", operational_criteria),
    "branded consumer goods": ("operational_criteria", operational_criteria),

    "webpage": ("authority_criteria", authority_criteria),
    "direct link to authority": ("authority_criteria", authority_criteria),
    "name of local authority": ("authority_criteria", authority_criteria),

    "provincial business license": ("license_criteria", license_criteria),
    "provincial food business license": ("license_criteria", license_criteria),
    "municipal business license": ("license_criteria", license_criteria),
    "municipal food business license": ("license_criteria", license_criteria),
    "retail license for CPG": ("license_criteria", license_criteria),

    "min distance to restaurant": ("distance_criteria", distance_criteria),
    "min distance to food truck": ("distance_criteria", distance_criteria),
    "proximity regulations": ("distance_criteria", distance_criteria),
    "non-food service proximity restrictions": ("distance_criteria", distance_criteria),
    "min distance proximity from other business": ("distance_criteria", distance_criteria),
}


# MAIN DOCUMENT PROCESSING

def extractDocument(text, filename, sourceType):
    """
    Core extraction pipeline.

    Steps:
    1. Clean text
    2. Split into sentences
    3. Match keywords per category
    4. Apply rule-based extraction
    5. Store results in MongoDB

    Args:
        text (str): document content
        filename (str): source identifier
        sourceType (str): 'txt', 'pdf', or 'url'
    """
    cleaned = cleanText(text)
    sentences = splitSentences(cleaned)
    results = {}

    for category, terms in KEYWORDS.items():
        matches = []

        for sentence in sentences:
            hits = extractKeywords(sentence.text, terms)
            if not hits:
                continue

            re_data = {}

            # Apply rule-based extraction if category is mapped
            if category in RULE_DISPATCH:
                key, func = RULE_DISPATCH[category]
                result = func(sentence)
                if result:
                    re_data[key] = result

            entry = {
                "sentence": sentence.text,
                "hits": hits
            }

            if re_data:
                entry["regex"] = re_data

            matches.append(entry)

        if matches:
            results[category] = matches

    # Save results to MongoDB
    upsertExtraction({
        "file": filename,
        "source": sourceType,
        "keyword_contexts": results
    })

    print(f"Extracted {sourceType}: {filename}")


# FILE HANDLERS

def extractTXT(filename):
    """Processes a TXT file."""
    path = join(FILEPATH, filename)

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    if not text:
        print("[Warning] empty txt")
        return

    extractDocument(text, filename, "txt")


def extractPDF(filename):
    """Processes a PDF file."""
    path = join(FILEPATH, filename)

    with open(path, "rb") as f:
        reader = PdfReader(f)
        text = "".join(page.extract_text() or "" for page in reader.pages)

    if not text.strip():
        print("[Warning] empty pdf")
        return

    extractDocument(text, filename, "pdf")


def extractURL(url: str):
    """
    Fetches and processes text from a URL.

    - Removes scripts, styles, and layout elements
    - Extracts visible text only
    """
    response = requests.get(url, timeout=10, headers={
        "User-Agent": "Mozilla/5.0"
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    if not text.strip():
        print(f"[Warning] empty url: {url}")
        return

    extractDocument(text, url, "url")


# ENTRY POINT

def extract():
    """
    Iterates through all files in FILEPATH and processes them.
    Supports TXT and PDF files.
    """
    print(dirname(realpath(__file__)))
    print(FILEPATH)

    for file_name in listdir(FILEPATH):
        if file_name.lower().endswith(".txt"):
            extractTXT(file_name)
        elif file_name.lower().endswith(".pdf"):
            extractPDF(file_name)


if __name__ == "__main__":
    extract()
import re

from Backend.Logic.mongo_db.extraction_collection import getAllExtractions
from Backend.Logic.mongo_db.classification_data_collection import upsertClassificationData

CANADIAN_CITIES = [
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria", "Windsor"
]

def checkForConflicts():
    collectData()
    
    # TODO: Finish checking for conflicts
    
    
        
def extractCityFromFilename(filename):
    filenameLower = filename.lower()
    for city in CANADIAN_CITIES:
        if city.lower() in filenameLower:
            return city
    
    return "unknown"

# TODO: Figure out a way to flag conflicts
def flagConflicts():
    pass

# TODO: Figure out a way to organize data extracted from text
def collectData():
    files = getAllExtractions()
    structuredData = []

    for file in files:
        filename = file.get("file", "unknown")
        city = extractCityFromFilename(filename)

        contexts = file.get("keyword_contexts", {})

        # Flatten all sentences
        sentences = []
        for category in contexts.values():
            for termSentences in category.values():
                sentences.extend(termSentences)

        # Deduplicate
        sentences = list(set([s.strip() for s in sentences if s.strip()]))

        # Structure of data
        data = {
            "filename": filename,
            "city": city,
            "application_fee": None,
            "licence_fee": None,
            "renewal_fee": None,
            "permit_fee": None,
            "insurance_amount": None,
            "max_operating_hours": None,
            "distance_requirement_meters": None,
            "zones": [],
            "parking_regulations": [],
            "health_inspection": False,
            "requirements": []
        }

        # Look for keywords and values that may be associated with it
        for sentence in sentences:
            lower = sentence.lower()

            # Fees
            if "application fee" in lower:
                value = _extract_money(sentence)
                if value:
                    data["application_fee"] = value

            if "licence fee" in lower or "license fee" in lower:
                value = _extract_money(sentence)
                if value:
                    data["licence_fee"] = value

            if "renewal fee" in lower:
                value = _extract_money(sentence)
                if value:
                    data["renewal_fee"] = value

            if "permit fee" in lower:
                value = _extract_money(sentence)
                if value:
                    data["permit_fee"] = value

            if "insurance" in lower:
                value = _extract_money(sentence)
                if value:
                    data["insurance_amount"] = value
                data["requirements"].append("insurance_required")

            hours = _extract_number(lower, r'(\d+)\s+hours?')
            if hours:
                data["max_operating_hours"] = hours

            meters = _extract_number(lower, r'(\d+)\s+(?:linear\s+)?metres?')
            if meters:
                data["distance_requirement_meters"] = meters

            if "zone" in lower:
                data["zones"].append(sentence)

            if "parking" in lower:
                data["parking_regulations"].append(sentence)

            if "health inspection" in lower or "public health" in lower:
                data["health_inspection"] = True
                data["requirements"].append("health_inspection_required")

            if "criminal record" in lower:
                data["requirements"].append("criminal_record_check_required")

            if "propane" in lower and "inspection" in lower:
                data["requirements"].append("propane_inspection_required")

            if "business licence" in lower or "business license" in lower:
                data["requirements"].append("business_licence_required")

        # Deduplicate list fields
        data["zones"] = list(set(data["zones"]))
        data["parking_regulations"] = list(set(data["parking_regulations"]))
        data["requirements"] = list(set(data["requirements"]))

        upsertClassificationData(data)
        

def _extract_money(text):
    match = re.search(r'\$\s?([\d,]+(?:\.\d{1,2})?)', text)
    if match:
        return float(match.group(1).replace(",", ""))
    return None

def _extract_number(text, pattern):
    match = re.search(pattern, text.lower())
    if match:
        return int(match.group(1))
    return None
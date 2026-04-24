import re

from Backend.Logic.mongo_db.extraction_collection import getAllExtractions
from Backend.Logic.mongo_db.classification_data_collection import upsertClassificationData, getAllClassificationsData

CANADIAN_CITIES = [
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria", "Windsor"
]

def checkForConflicts():
    collectData() # Make data from classifier into type data and store in MongoDB
    
    data = getAllClassificationsData()
    
    flagConflicts(data)


def flagConflicts(data_files):
    conflicts = []
    
    for i, file1 in enumerate(data_files):
        for file2 in data_files[i + 1:]:
            if file1.get("city") != file2.get("city"):
                continue
            
            for key in file1.keys():

                if key in ["filename", "city", "_id"]:
                    continue

                val1 = file1.get(key)
                val2 = file2.get(key)

                if val1 is None or val2 is None:
                    continue

                # Handle list comparisons
                if isinstance(val1, list) and isinstance(val2, list):
                    if set(val1) != set(val2):
                        conflicts.append({
                            "city": file1["city"],
                            "field": key,
                            "file1": file1["filename"],
                            "value1": val1,
                            "file2": file2["filename"],
                            "value2": val2
                        })
                else:
                    if val1 != val2:
                        conflicts.append({
                            "city": file1["city"],
                            "field": key,
                            "file1": file1["filename"],
                            "value1": val1,
                            "file2": file2["filename"],
                            "value2": val2
                        })

    for c in conflicts:
        print(
            f"Conflict in {c['city']} for {c['field']}:\n"
            f"  {c['file1']} -> {c['value1']}\n"
            f"  {c['file2']} -> {c['value2']}\n"
        )

    return conflicts             


def collectData():
    files = getAllExtractions()

    for file in files:
        filename = file.get("file", "unknown")
        city = extractCityFromFilename(filename)

        contexts = file.get("keyword_contexts", {})

        # Flatten all hits (only sentences with keyword hits)
        sentences = []

        for category_list in contexts.values():            # category_list is a list of objects
            for item in category_list:                     # each object in the list
                hits = item.get("hits", {})                # hits is a dict of keyword -> list of sentences
                for hit_list in hits.values():
                    sentences.extend(hit_list)            # add all hit sentences

        # Deduplicate
        sentences = list({s.strip() for s in sentences if s.strip()})
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
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    return None


def extractCityFromFilename(filename):
    filenameLower = filename.lower()
    for city in CANADIAN_CITIES:
        if city.lower() in filenameLower:
            return city
    
    return "unknown"
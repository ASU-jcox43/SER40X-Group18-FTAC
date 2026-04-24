import re
from datetime import datetime
from Backend.Logic.municipality_profile.profile_manager import createMunicipalityProfile
from Backend.Logic.mongo_db.profile_collection import upsertProfile
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions


CITIES = {
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria",
    "Regina", "Saskatoon", "Kelowna", "Abbotsford", "Burnaby", 
    "Phoenix", "Windsor","Mississauga", "york", "Yellowknife",
}


def addProfile(**kwargs):
    """Adds the municipality profile into the mongodb database
    """
    
    profile = createMunicipalityProfile(**kwargs)
    # Save/update the profile
    upsertProfile(profile)
    print(f"Upserted profile for {profile['Geographic']['City']}")

def findInformation(extraction: dict) -> dict:
    """Searches through keyword contexts for references to any attirbute
    of the municipality profile

    Args:
        extraction (dict): Extraction JSON with file and keyword contexts

    Returns:
        dict: All the attributes function could find for municpality profile
    """
    
    filename = extraction["file"]
    contexts = extraction["keyword_contexts"]

    title = getTitle(filename)
    
    # Flatten all sentences from every keyword context bucket
    seen = set()
    all_sentences = []

    for bucket in contexts.values():
        if not bucket:
            continue

        # Case 1: bucket is a dict (normal case)
        if isinstance(bucket, dict):
            for keyword_list in bucket.values():
                if not keyword_list or not isinstance(keyword_list, list):
                    continue

                for s in keyword_list:
                    if isinstance(s, str) and s.strip() and s not in seen:
                        seen.add(s)
                        all_sentences.append(s.strip())

        # Case 2: bucket is already a list (unexpected but happening)
        elif isinstance(bucket, list):
            for s in bucket:
                if isinstance(s, str) and s.strip() and s not in seen:
                    seen.add(s)
                    all_sentences.append(s.strip())

    combined = " ".join(all_sentences).lower()

    # Search for City reference based on CITIES dictionary
    city = None
    cities_lower = {c.lower(): c for c in CITIES}  # lookup: lowercase → canonical
    sorted_candidates = sorted(cities_lower.items(), key=lambda x: len(x[0]), reverse=True)
    
    for lower_candidate, canonical in sorted_candidates:
        for s in all_sentences:
            if re.search(rf"\b{re.escape(lower_candidate)}\b", s, re.IGNORECASE):
                city = canonical
                break
        if city:
            break

    # Fallback: match domain from file URL against CITIES.
    # Only runs if file is a real URL (starts with http) to avoid
    # picking up malformed _id values like "Torontohttps".
    if not city and filename and filename.startswith("http"):
        domain = re.sub(r"https?://|/.*", "", filename).replace("www.", "")
        domain_lower = domain.split(".")[0].lower()
        if domain_lower in cities_lower:
            city = cities_lower[domain_lower]

    province_hints = {
        "cities act":                   "Saskatchewan",
        "municipal act":                "British Columbia",
        "municipal government act":     "Alberta",
        "planning act":                 "Ontario",
        "municipal affairs act":        "Nova Scotia",
        "municipalities act":           "Manitoba",
    }
    province = None
    for hint, prov in province_hints.items():
        if hint in combined:
            province = prov
            break

    office_patterns = [
        (r"office of the city clerk",        "City Clerk"),
        (r"bylaw enforcement",               "Bylaw Enforcement Office"),
        (r"licens",                          "Licensing Office"),
        (r"permit",                          "Permit Office"),
        (r"public health|food safety",       "Public Health / Food Safety Office"),
        (r"fire department|fire service",    "Fire Department"),
        (r"police",                          "Police / Board of Police Commissioners"),
        (r"planning|development application","Planning & Development Office"),
    ]
    
    contacts = []
    seen_labels = set()
    for s in all_sentences:
        for pattern, label in office_patterns:
            if re.search(pattern, s, re.IGNORECASE) and label not in seen_labels:
                contacts.append({
                    "Office": label,
                    "Notes": s.strip(),
                    "Website": filename or None,
                })
                seen_labels.add(label)

    return {
        # --- Directly inferred from extraction ---
        "name":               f"City of {city}" if city else None,
        "title":                title,
        "file":                 filename,
        "city":                 city,
        "province":             province,
        "contacts":             contacts,
        "friendlinessScore": None,
        "friendlinessScoreBreakdown": None,

        # --- Requires external sources (Statistics Canada, GIS, etc.) ---
        "fb_type":              None,
        "region":               None,
        "population":           None,
        "avgAge":               None,
        "ethnicityComposition": {},
        "houseSize":            None,
        "educationLevel":       [],
        "income":               None,
        "min_wage":             None,
        "comm_tax_rates":       None,
        "lat":                  None,
        "long":                 None,
        "areaSqMiles":          None,
        "popSqMile":            None,
        "adjMunicipalities":    [],
    }


def getTitle(filename: str) -> str:
    """Searches for document type through file name

    Args:
        filename (str): Name of the file

    Returns:
        str: file type
    """
    
    filename = filename.lower()

    if "bylaw" in filename or "by-law" in filename:
        return "bylaw"
    
    if "license" in filename or "permit" in filename:
        return "license"
    
    if "guide" in filename:
        return "guide"

    if "municipal code" in filename:
        return "municipal code"
    
    if "brochure" in filename:
        return "brochure"
    
    return "other"

if __name__ == "__main__":
    docs = getAllExtractions()

    for doc in docs:
        profile_data = findInformation(doc)

        profile_data["last_updated"] = datetime.now().isoformat()

        addProfile(**profile_data)
        print(f"processed {doc['file']}")
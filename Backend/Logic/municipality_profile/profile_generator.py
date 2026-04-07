import re
from datetime import datetime
from Backend.Logic.municipality_profile.profile_manager import createMunicipalityProfile
from Backend.Logic.mongo_db.profile_collection import upsertProfile
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions


CITIES = {
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria",
    "Regina", "Saskatoon", "Kelowna", "Abbotsford", "Burnaby", 
    "Phoenix", "Windsor",
}


def addProfile(**kwargs):
    profile = createMunicipalityProfile(**kwargs)
    # Save/update the profile
    upsertProfile(profile)
    print(f"Upserted profile for {profile['Geographic']['City']}")


def findInformation(extraction: dict) -> dict:
    source_url = extraction["file"]
    contexts = extraction["keyword_contexts"]

    # --- Flatten all sentences from every keyword context bucket ---
    seen = set()
    all_sentences = []
    for bucket in contexts.values():
        for entry in bucket:
            s = entry.get("sentence", "")
            if s and s not in seen:
                seen.add(s)
                all_sentences.append(s)

    combined = " ".join(all_sentences).lower()

    # --- City (matched against predefined CITIES list) ---
    # Always inserts the canonical CITIES spelling regardless of how it appears in text.
    # Sort by length descending so multi-word cities (e.g. "Quebec City") match before
    # single-word substrings (e.g. "Quebec").
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
    if not city and source_url and source_url.startswith("http"):
        domain = re.sub(r"https?://|/.*", "", source_url).replace("www.", "")
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
                    "Website": source_url or None,
                })
                seen_labels.add(label)

    # --- Bylaw list (for friendliness score breakdown) ---
    bylaw_pattern = re.compile(
        r"([A-Za-z &]+bylaw)\s+no\.\s+([\d\-]+)\s+(.*?)(?=\.\s|$)",
        re.IGNORECASE
    )
    bylaws = []
    seen_numbers = set()
    for s in all_sentences:
        for match in bylaw_pattern.finditer(s):
            number = match.group(2).strip()
            if number not in seen_numbers:
                bylaws.append({
                    "name": match.group(1).strip().title(),
                    "number": number,
                    "description": match.group(3).strip(),
                })
                seen_numbers.add(number)

    # --- Scoring notes ---
    score_keywords = ["bylaw", "zoning", "licens", "permit", "enforcement",
                      "fee", "violation", "appeal", "standard", "tax"]
    scoring_notes = []
    seen_notes = set()
    for s in all_sentences:
        if any(kw in s.lower() for kw in score_keywords) and s not in seen_notes:
            scoring_notes.append(s.strip())
            seen_notes.add(s)

    return {
        # --- Directly inferred from extraction ---
        "name":               f"City of {city}" if city else None,
        "city":               city,
        "province":           province,
        "contacts":           contacts,
        "friendlinessScore": {
            "Foundational":              None,
            "Licensing Requirements":    None,
            "Operations & Restrictions": None,
        },
        "friendlinessScoreBreakdown": {
            "source":            source_url,
            "bylaws_identified": bylaws,
            "scoring_notes":     scoring_notes,
        },

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


if __name__ == "__main__":
    docs = getAllExtractions()

    for doc in docs:
        profile_data = findInformation(doc)

        profile_data["last_updated"] = datetime.now().isoformat()

        addProfile(**profile_data)
        print(f"processed {doc['file']}")
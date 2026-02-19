"""
Document classifier file.

This module parses each word to determine
proper classification based on a set of keywords and how often they appear.

    Usage example:

    text = "Purchase a permit or a license."
    classify_text(text)
"""

import re
from Backend.Logic.classifier.utils import check_for_conflicts
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions
from Backend.Logic.mongo_db.classification_collection import upsertClassification, getAllClassifications

# Our list of keywords that we can customize when classifying documents in a dictionary
KEYWORDS = {
    "Legal and Bylaws": {
        "bylaw": 3,
        "by-law": 3,
        "regulation": 2,
        "ordinance": 3,
        "section": 1,
        "penalty": 2,
        "fine": 3,
        "enforcement": 2,
        "compliance": 2,
        "amend": 2,
        "repeal": 2,
        "supersede": 3,
    },
    "Licensing": {
        "license": 2,
        "licence": 2,
        "permit": 2,
        "application": 1,
        "registration": 1,
        "renewal": 2,
        "certificate": 1,
        "business licence": 3,
        "inspection required": 3,
        "approval": 1,
    },
    "Zoning": {
        "zoning": 3,
        "zone": 2,
        "land use": 3,
        "site plan": 2,
        "occupancy": 2,
        "setback": 2,
        "parking": 1,
        "traffic": 1,
        "noise": 1,
        "district": 2,
    },
    "Food Safety": {
        "food safety": 3,
        "public health": 2,
        "sanitation": 2,
        "temperature": 2,
        "food handler": 2,
        "haccp": 3,
        "inspection report": 2,
        "kitchen": 1,
        "sanitary": 2,
        "health officer": 3,
    },
    "Risk and Fire": {
        "fire code": 3,
        "propane": 3,
        "suppression": 2,
        "sprinkler": 2,
        "extinguisher": 2,
        "flammable": 2,
        "hazard": 2,
        "gas line": 3,
        "fire department": 3,
    },
    "General": {
        "overview": 1,
        "information": 1,
        "guide": 1,
        "homepage": 1,
        "requirements": 1,
        "process": 1,
    }
}

CITIES = {
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria"
}

def classify_text(text):
    """
    Classify a string of text into a category and confidence rating based on matches to keywords.

    This function searches for the keywords in the given text, counts each appearance, then assigns
    a classification based on the best matching category with the most counts.

    Args:
        text: The text string that will be classified.

    Returns:
        A tuple with:
            - category (str): The best matching category name, otherwise N/A for no matches.
            - confidence (float): The numeric rating from 0.0-1.0 determined by number of occurrences in the
            best category versus the total number of occurrences.
        Example:
            [Permit Documents, 0.75].
    """
    lowercase = text.lower()
    words = re.findall(r"\b\w+\b", lowercase)
    scores = {}

    # for each category and keyword in our keywords list,
    # we score the number of matches we found looking through the text
    # if we don't find anything, we leave it blank (N/A) with a confidence of 0.0
    for category, keywords in KEYWORDS.items():
        total_score = 0

        for term, weight in keywords.items():
            # If term is multi-word phrase
            if " " in term:
                count = lowercase.count(term)
            else:
                count = words.count(term)

            total_score += count * weight

        if total_score > 0:
            scores[category] = total_score

    if not scores:
        return ["N/A"], 0.0

    # We pick the top categories in scores based on number of matches,
    # and calculate our confidence rate based on the number of matches vs the total number of terms
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    max_score = sorted_scores[0][1]
    
    top_categories = [ # Only include categories that are close to the top score
        category for category, score in sorted_scores
        if score >= max_score * 0.7
    ]
    
    confidence = max_score / sum(scores.values())
    
    return top_categories, round(confidence, 2)


def classify_files():
    """
    Classify all files in a designated folder into the correct categories.

    This function goes through all the files in the extraction collection in the MongoDB Database

    Returns:
        A list of results in JSON pretty print format including:
            - filename: The name of the file.
            - Top Categories: The top classifying categories.
            - confidence: The float score of the category.
        Example:
            [filename: examplefile.pdf,
            Top Categories: [
                Legal and Bylaws,
                Licensing
                ],
            confidence: 0.87]

    Raises:
        FileNotFoundError: an error occurred trying to read a file.
    """

    docs = getAllExtractions()
    
    for doc in docs:
        result = []
        # flatten keyword_contexts -> text string
        contexts = []
        for terms in doc.get("keyword_contexts", {}).values():
            for arr in terms.values():
                contexts.extend(arr)

        text = " ".join(contexts)

        top_categories, confidence = classify_text(text)
        filename = doc.get("file", "unkown")
        result = {
            "filename": filename,
            "Top Categories": top_categories,
            "confidence": confidence
        }
        
        upsertClassification(result)


if __name__ == "__main__":
    classify_files()
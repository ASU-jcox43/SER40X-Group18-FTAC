"""
Document classifier file.

This module parses each word to determine
proper classification based on a set of keywords and how often they appear.

    Usage example:

    text = "Purchase a permit or a license."
    classify_text(text)
"""


import os
import json
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions
from Backend.Logic.mongo_db.classification_collection import upsertClassification

# Our list of keywords that we can customize when classifying documents in a dictionary
KEYWORDS = {
    "Legal and Bylaws": [
        "bylaw", "by-law", "act", "regulation", "ordinance",
        "enacted", "section", "article", "penalty", "fine",
        "enforcement", "compliance", "amend", "repeal", "supersede"
    ],

    "Licensing": [
        "license", "licence", "permit", "application",
        "registration", "renewal", "certificate",
        "business licence", "approval", "inspection required"
    ],

    "Zoning": [
        "zoning", "zone", "land use", "site plan",
        "occupancy", "setback", "parking", "traffic",
        "noise", "geographic", "district"
    ],

    "Food Safety": [
        "food safety", "public health", "sanitation",
        "temperature", "food handler", "haccp",
        "inspection report", "kitchen", "sanitary",
        "health officer"
    ],

    "Risk and Fire": [
        "fire code", "propane", "suppression",
        "sprinkler", "extinguisher", "flammable",
        "hazard", "gas line", "fire department"
    ],

    "General": [
        "overview", "information", "guide",
        "homepage", "requirements", "process"
    ]
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
    scores = {}

    # for each category and keyword in our keywords list,
    # we count the number of matches we found looking through the text
    # if we don't find anything, we leave it blank (N/A) with a confidence of 0.0
    for category, keywords in KEYWORDS.items():
        count = 0
        for term in keywords:
            count += lowercase.count(term)
        if count > 0:
            scores[category] = count

    if not scores:
        return ["N/A"], 0.0

    # We pick the top categories in scores based on number of matches,
    # and calculate our confidence rate based on the number of matches vs the total number of terms
    # Pick the top categories to cover conflicting categories for one document
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if sum(scores.values()) == 0.0:
        confidence = 0.0
    else:
        top_categories = [c for c, _ in sorted_scores[:2]]
        confidence = sorted_scores[0][1] / sum(scores.values())
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

        result = {
            "filename": doc.get("file", "unknown"),
            "Top Categories": top_categories,
            "confidence": confidence
        }
    
        FILE_DIR = "Backend/Logic/classifier/classifications"
        os.makedirs(FILE_DIR, exist_ok=True)

        # Create safe filename
        base_filename = doc.get("file", "unknown")
        name_without_ext = os.path.splitext(base_filename)[0]
        output_filename = f"{name_without_ext}_classification.json"

        output_path = os.path.join(FILE_DIR, output_filename)

        upsertClassification(result)
        
        with open(output_path, "w") as config_file:
            json.dump(result, config_file, indent=2)
    
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    classify_files()
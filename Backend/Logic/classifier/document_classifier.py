"""
Document classifier file.

This module takes in text from documents, and parses each word to determine
proper classification based on a set of keywords and how often they appear.

    Usage example:

    text = "Purchase a permit or a license."
    classify_text(text)
"""


import json
import re
from pathlib import Path
from utils import extract_text

# Our list of keywords that we can customize when classifying documents in a dictionary
KEYWORDS = {"Permit Documents": ["permit", "license", "authorization", "inspection"],
            "Financial Documents": ["invoice", "payment", "tax", "taxes"],
            "Legal Documents": ["agreement", "contract", "terms", "bylaw", "law"],
            "Technical Documents": ["specification", "manual", "design", "requirements"]
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
        count = sum(len(re.findall(rf'\b{term}\b', lowercase)) for term in keywords)
        if count > 0:
            scores[category] = count

    if not scores:
        return "N/A", 0.0

    # We pick the category in scores that has the highest number of matches,
    # and calculate our confidence rate based on the number of matches vs the total number of terms
    bestCategory = max(scores, key=scores.get)
    if sum(scores.values()) == 0.0:
        confidence = 0.0
    else:
        confidence = scores[bestCategory] / sum(scores.values())
    return bestCategory, round(confidence, 2)


def classify_files(folder_path):
    """
    Classify all files in a designated folder into the correct categories.

    This function goes through all the files in a specified directionry, extracts the text
    using the "extract_text" function in utils.py, then classifies each using "classify_text."

    Args:
        folder_path: A string determining the path to the document directory.

    Returns:
        A list of results in JSON pretty print format including:
            - filename: The name of the file.
            - category: The classifying category.
            - confidence: The float score of the category.
        Example:
            [filename: examplefile.pdf,
            category: Permits Document,
            confidence: 0.87]

    Raises:
        FileNotFoundError: an error occurred trying to read a file.
    """

    results = []
    folder = Path(folder_path)

    # Here we go through all the files, and run the extract_text function to get their text.
    # We then run classify_text on that found text to get the category that best matched and
    # its confidence score, otherwise it gives an error if the file couldn't be read.
    for file_path in folder.glob("*.*"):
        try:
            text = extract_text(file_path)
            category, confidence = classify_text(text)
            results.append({
                "filename": file_path.name,
                "category": category,
                "confidence": round(confidence, 2)
            })
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    filename = "classifications.json"
    with open(filename, "w") as config_file:
        json.dump(results, config_file, indent=2)
    
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    classify_files("../analysis_ready")

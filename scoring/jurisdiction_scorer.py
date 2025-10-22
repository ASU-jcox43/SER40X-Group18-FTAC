"""
Jurisdiction scoring file.

This module takes a JSON file, and checks each category with a regular expression pattern,
adding points to determine a final score.

"""

import json
import re
from pathlib import Path

# These are really rough around the edges but hopefully can be tweaked later.
# Re is not easy...
REGEX_PATTERNS = {
    "webpage": r"\.gov",
    "checklist": r"checklist",
    "guide to license": r"guide",
    "bylaws": r"bylaw",
    "penalties": r"fine|fee",
    "provincial business license": r"provincial business license",
    "provincial food business license": r"provincial food business licence",
    "municipal business license": r"municipal business license",
    "municipal food business license": r"municipal food business license",
    "retail license for CPG": r"consumer packaged good|CPG",
    "curbside vending": r"curbside vending",
    "parking fees": r"parking fee",
    "noise bylaws": r"noise|noise bylaws|sound",
    "traffic bylaws": r"traffic bylaw",
    "operation hours": r"operation hours",
    "branded consumer goods": r"branded consumer goods",
    "private property operation": r"private property",
    "proximity regulations": r"proximity regulation",
    "min distance to restaurant": r"distance.*restaurant(s)?|restaurant(s)?.*distance",
    "min distance to food truck": r"food truck.*located.*from.*food truck",
    "non-food service proximity restrictions": r"proximity regulation(s)?.*non-food|non-food.*proximity regulation(s)?",
    "min distance proximity from other business": r"distance.*business|business.*distance",
    "num food trucks allowed in geographic area": r"number of food trucks allowed",
    "parking locations": r"designated parking",
    "additional private restrictions": r"private.*additional restriction(s)?",
    "name of local authority": r"local authority",
    "direct link to authority": r"contact.*at",
    "insurance requirements": r"insurance",
    "physical requirements for trucks": r"truck(s)?.*must have",
    "exterior appearance guidelines": r"exterior appearance"
}


def score_categories(category, text):
    """
        Checks if a category has a match with the regular expression.

        This function uses the regex pattern dictionary to check if a category has a match with a phrase.

        Args:
            category: The category that will be checked.
            text: The text string that will be referenced.

        Returns:
            True or False depending on if a match was found.
        """
    pattern = REGEX_PATTERNS.get(category)
    if not pattern:
        return False
    return bool(re.search(pattern, text, re.IGNORECASE))


def score_json_file(path):
    """
        Calculates the friendliness score for a single JSON file.

        This function opens a JSON file and goes through each category and increases the score
        if a match with the regex patterns is found.

        Args:
            path: The file path to the folder of JSON files.

        Returns:
            The score rounded to two decimal points.
    """

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    score = 0
    for category, terms, in data.get("keyword_contexts", {}).items():
        found = False
        for term, sentences in terms.items():
            for sentence in sentences:
                if score_categories(category, sentence):
                    score += 1
                    found = True
                    break
            if found:
                    break

    score /= 30
    score *= 100
    return round(score, 2)


def score_jurisdictions(path):
    """
        Iterates through all JSON files in a folder.

        This function is what goes through each file in a directory and runs the scorer on each.

        Args:
            path: The file path to the folder of JSON files.
    """
    results = {}
    folder = Path(path)

    for file_path in folder.glob("*.json"):
        try:
            score = score_json_file(file_path)
            results[file_path.name] = score
            print(f"{file_path.name} has a friendliness score of: {score}%")
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    filename = "friendliness_summary.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    score_jurisdictions("../analysis_ready")

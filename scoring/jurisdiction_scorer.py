"""
Jurisdiction scoring file.

This module takes a JSON file, and checks each category with a regular expression pattern,
adding points to determine a final score.

"""

import json
import os
import re
import sys
from pathlib import Path

def score_categories(text, category, model:dict):
    """
        Checks if a category has a match with the regular expression.

        This function uses the regex pattern dictionary to check if a category has a match with a phrase.

        Args:
            text: The text string that will be referenced.
            category: The category that will be checked.
            model: The scoring model dictionary containing the category.

        Returns:
            True or False depending on if a match was found.
        """
    pattern = model.get(category)
    if not pattern:
        return False
    return bool(re.search(pattern, text, re.IGNORECASE))


def score_json_file(path, model:dict):
    """
        Calculates the friendliness score for a single JSON file.

        This function opens a JSON file and goes through each category and increases the score
        if a match with the regex patterns is found.

        Args:
            path: The file path to the folder of JSON files.
            model: The scoring model that will be used.

        Returns:
            The score rounded to two decimal points.
    """

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    score = 0

    for category, terms, in data.get("keyword_contexts", {}).items():
        for term, sentences in terms.items():
            for sentence in sentences:
                if score_categories(sentence, category, model):
                    score += 1
                    break
                else:
                    continue
                break
    score = (score / len(model)) * 100
    return round(score, 2)


def score_jurisdictions(path, model:dict):
    """
        Iterates through all JSON files in a folder.

        This function is what goes through each file in a directory and runs the scorer on each.

        Args:
            path: The file path to the folder of JSON files.
            model: The scoring model that will be used.
    """
    results = {}
    folder = Path(path)

    for file_path in folder.glob("*.json"):
        try:
            score = score_json_file(file_path, model)
            results[file_path.name] = score
            print(f"{file_path.name} has a friendliness score of: {score}%")
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    filename = "friendliness_summary.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))

def import_model(path):
    return json.load(open(path, "r"))

if __name__ == "__main__":
    scoring_model = import_model("scoring_models/foodtruck.json")
    score_jurisdictions("../analysis_ready", scoring_model)
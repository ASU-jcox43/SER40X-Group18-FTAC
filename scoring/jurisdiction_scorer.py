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
from typing import Iterable


def score_categories(text, category:str, model:dict[str, str]):
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
    print(f"MODEL {model} MODEL")
    pattern = model.get(category)
    if not pattern:
        return False
    return bool(re.search(pattern, text, re.IGNORECASE))

def score_json_file(path, models:dict[str, dict[str, str]]):
    """
        Calculates the friendliness score for a single JSON file.

        This function opens a JSON file and goes through each category and increases the score
        if a match with the regex patterns is found.

        Args:
            path: The file path to the folder of JSON files.
            models: The scoring models that will be used.

        Returns:
            The score rounded to two decimal points.
    """

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scores = {model: 0 for model in models}

    for category, terms, in data.get("keyword_contexts", {}).items():
        for term, sentences in terms.items():
            for sentence in sentences:
                for model in models.keys():
                    if score_categories(sentence, category, models[model]):
                        scores[model] += 1
                        break
                    else:
                        continue
    print(scores.items())
    return {model:round((score/len(models[model].keys()))*100, 2) for (model, score) in scores.items()}

def score_jurisdictions(path, models:dict[str, dict[str, str]]):
    """
        Iterates through all JSON files in a folder.

        This function is what goes through each file in a directory and runs the scorer on each.

        Args:
            path: The file path to the folder of JSON files.
            models: The scoring models that will be used.
    """
    results = {}
    folder = Path(path)

    for file_path in folder.glob("*.json"):
        score = score_json_file(file_path, models)
        try:
            score = score_json_file(file_path, models)
            results[file_path.name] = score
            print(f"{file_path.name} has a friendliness score of: {score}%")
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    filename = "friendliness_summary.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))

def import_model(path) -> dict:
    """
    Used to import a scoring model
    :param path: Path to a scoring model in json format. Each key is a scoring category and the values are regular expressions that are used to calculate the score. Example input: ``{"score_category1": "regex1", "score_category2": "regex2"}``
    :return: A scoring model dictionary
    """
    return json.load(open(path, "r"))

if __name__ == "__main__":
    scoring_models = {}
    scoring_models_dir = Path("scoring_models")
    for scoring_model_file in scoring_models_dir.glob("*.json"):
        scoring_models[str(scoring_model_file)[len(scoring_models_dir.name)+1:-5]] = import_model(scoring_model_file)
    score_jurisdictions("../analysis_ready", scoring_models)
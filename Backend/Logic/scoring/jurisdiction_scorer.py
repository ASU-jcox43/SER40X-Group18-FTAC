"""
Jurisdiction scoring file.

This module takes a JSON file, and checks each category with a regular expression pattern,
adding points to determine a final score.

"""

import json
import operator
import re
from operator import concat
from pathlib import Path
import flatdict
from functools import reduce


def score_categories(text, category: str, model: dict[str, str]):
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


def score_json_file(path, model: dict[str, str]):
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

    keyword_sentences = flatdict.FlatDict(data.get("keyword_contexts", {}), delimiter='/')

    matched_keywords = []
    for sentence_list in keyword_sentences.keys():
        keyword = sentence_list.split('/')[0]
        if keyword not in matched_keywords and isinstance(keyword_sentences[sentence_list], list):
            paragraph = reduce(lambda x, y: f"{x} {y}", keyword_sentences[sentence_list])
            if score_categories(paragraph, keyword, model):
                matched_keywords.append(keyword)
    return round((len(matched_keywords) / len(model.keys())) * 100, 2)


def score_jurisdictions(path, models: dict[str, dict[str, str]]):
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
        results[file_path.name] = {}
        try:
            for model in models.keys():
                score = score_json_file(file_path, models[model])
                results[file_path.name][model] = score
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    filename = "friendliness_summary.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)


def import_models(path: str):
    """
    Imports all models from the file path.
    :param path: Directory containing the scoring models. Scoring models are in json, each key is a scoring category and the values are regular expressions that are used to calculate the score. Example input: ``{"score_category1": "regex1", "score_category2": "regex2"}``
    :return: A dictionary of scoring model dictionaries. The keys are the file names without ".json"
    """
    scoring_models = {}
    scoring_models_dir = Path(path)
    for scoring_model_file in scoring_models_dir.glob("*.json"):
        scoring_models[str(scoring_model_file)[len(scoring_models_dir.name) + 1:-5]] = json.load(
            open(scoring_model_file, 'r'))
    return scoring_models


if __name__ == "__main__":
    # TODO: replace with MongoDB code
    score_jurisdictions("../analysis_ready", import_models("scoring_models"))

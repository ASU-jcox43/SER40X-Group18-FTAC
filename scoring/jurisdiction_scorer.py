"""
Jurisdiction scoring file.

This module takes a JSON file, and checks each category with a regular expression pattern,
adding points to determine a final score.

"""

import json
import re

# This is hard coded right now for testing, but will be changed later.
with open("testing_file.json", "r", encoding="utf-8") as f:
    data = json.load(f)

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

# Right now, this is just by itself since we are only using the one test JSON file.
# Later, it will be similar to the classifier in that it will go through a whole folder.
score = 0
for category, terms, in data["keyword_contexts"].items():
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
print(f"This jurisdiction has a friendliness score of {round(score, 2)}%")
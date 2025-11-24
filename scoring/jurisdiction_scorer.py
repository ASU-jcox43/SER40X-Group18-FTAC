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
KEYWORDS = {
  "webpage": [".gov", ".ca", "municipality", "city of", "regional district"],
  "checklist": ["checklist", "requirements list", "required documents"],
  "guide to license": ["guide", "how to apply", "licensing process", "application process"],
  "bylaws": ["bylaw", "regulation", "municipal code", "ordinance"],
  "penalties": ["fine", "fee", "penalty", "violation", "infraction"],
  "provincial business license": ["provincial business license", "provincial permit", "provincial approval", "provincial business name certificate"],
  "provincial food business license": ["provincial food business license", "food establishment permit", "provincial food vendor license"],
  "municipal business license": ["municipal business license", "local business permit", "city business license"],
  "municipal food business license": ["municipal food business license", "mobile food vendor license", "street food vendor license"],
  "retail license for CPG": ["consumer packaged good", "CPG", "retail goods", "branded retail products"],
  "curbside vending": ["curbside vending", "street vending", "mobile vending", "sidewalk vending"],
  "parking fees": ["parking fee", "metered parking", "vending zone", "designated vending area"],
  "noise bylaws": ["noise", "noise bylaw", "sound regulation", "amplified sound"],
  "traffic bylaws": ["traffic bylaw", "traffic regulation", "vehicle restriction", "road use", "traffic act"],
  "operation hours": ["operating hours", "business hours", "hours of operation", "time limit", "maximum duration", "hours at any one time"],
  "branded consumer goods": ["branding", "branded products", "product labeling", "consumer goods"],
  "private property operation": ["private property", "private lot", "owner permission", "property consent"],
  "proximity regulations": ["proximity regulation", "distance restriction", "buffer zone", "proximity limit"],
  "min distance to restaurant": ["distance to restaurant", "separation from restaurant", "nearby restaurant restriction", "from an open and operating restaurant"],
  "min distance to food truck": ["distance to other food trucks", "food truck spacing", "vendor proximity"],
  "non-food service proximity restrictions": ["proximity restriction", "non-food vendor proximity", "distance from other vendors"],
  "min distance proximity from other business": ["proximity to other business", "distance between vendors"],
  "num food trucks allowed in geographic area": ["number of food trucks allowed", "maximum food trucks per area", "vendor density limit", "food trucks per block"],
  "parking locations": ["designated parking", "allowed parking", "approved vending location", "vending area", "public road vending"],
  "additional private restrictions": ["private restrictions", "additional property rules", "landowner conditions"],
  "name of local authority": ["local authority", "licensing department", "municipal licensing office", "city clerk", "regulatory agency"],
  "direct link to authority": ["reach out", "contact", "reach", "office", "call", "email", "phone"],
  "insurance requirements": ["insurance", "liability coverage", "certificate of insurance", "proof of insurance"],
  "physical requirements for trucks": ["vehicle requirements", "truck must have", "equipment standards", "vehicle condition", "inspection requirements", "plate number", "license number", "business name", "client's name"],
  "exterior appearance guidelines": ["paint", "painted", "appearance", "vehicle signage", "branding on truck", "exterior look", "color", "color contrast", "colour", "colour contrast", "identification markings"]
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
    pattern = KEYWORDS.get(category)
    if not pattern:
        return False
    for term in pattern:
        if term in text:
            return True
    return False



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
        for term, sentences in terms.items():
            for sentence in sentences:
                if score_categories(category, sentence):
                    score += 1
                    break
                else:
                    continue
            break
    score = (score / len(KEYWORDS)) * 100
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

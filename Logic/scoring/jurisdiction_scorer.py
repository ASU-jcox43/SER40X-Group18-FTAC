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
    "webpage": r"\.(gov|ca|org|com)\b",
    "checklist": r"\b(checklist|required\s+documents?|supporting\s+documents?)\b",
    "guide to license": r"\b(guide|how\s+to\s+apply|application\s+instructions?)\b",
    "bylaws": r"\b(by[-]?law(s)?|regulation(s)?|municipal\s+code|chapter\s+\d+)\b",
    "penalties": r"\b(fine(s)?|fee(s)?|charge(s)?|penalt(y|ies))\b",
    "provincial business license": r"\b(provincial\s+(business|vendor|operator)\s+licen[cs]e)\b",
    "provincial food business license": r"\b(provincial\s+(food|restaurant|mobile|refreshment)\s+licen[cs]e)\b",
    "municipal business license": r"\b(municipal\s+(business|vendor|operator)\s+licen[cs]e)\b",
    "municipal food business license": r"\b(municipal\s+(food|restaurant|mobile|refreshment)\s+licen[cs]e)\b",
    "retail license for CPG": r"\b(consumer\s+packaged\s+good(s)?|CPG|retail\s+product)\b",
    "curbside vending": r"\b(curbside|street|mobile)\s+vending\b",
    "parking fees": r"\b(parking\s+(fee|rate|permit|payment|meter|zone|ticket))\b",
    "noise bylaws": r"\b(noise|sound|amplified\s+music|noise\s+by[-]?law)\b",
    "traffic bylaws": r"\b(traffic\s+by[- ]?law|act|road\s+closure|vehicle\s+restriction)\b",
    "operation hours": r"\b((operation|operating|business|service)\s+hour(s)?|hour(s)?\s+of\s+("r"operation|operations?|business|service))\b",
    "branded consumer goods": r"\b(brand(ed)?|logo|branded\s+consumer\s+good(s)?)\b",
    "private property operation": r"\b(private\s+(property|lot|land|premises))\b",
    "proximity regulations": r"\b(proximity\s+(regulation|rule|restriction|limit))\b",
    "min distance to restaurant": r"\b(proximity|distance|restriction)\b.*\b(non[-]?food|retail|service)\b|\b(from.*restaurant)\b",
    "min distance to food truck": r"\b(distance|proximity|buffer)\b.*\b(food\s+truck(s)?)\b|\b(food\s+truck(s)?)\b.*\b(distance|proximity|buffer)\b",
    "non-food service proximity restrictions": r"\b(proximity|distance|restriction)\b.*\b(non[-]?food|retail|service)\b",
    "min distance proximity from other business": r"\b(distance|proximity|buffer)\b.*\b(business(es)?|vendor(s)?)\b",
    "num food trucks allowed in geographic area": r"\b(number|limit|maximum|quota)\b.*\b(food\s+truck(s)?)\b|\b(food truck(s)? per.*)\b",
    "parking locations": r"\b((parking\s+(location(s)?|spot(s)?|zone(s)?|area(s)?|designation(s)?|space(s)?|lot(s)?|place(s)?|area(s)?\s+allowed))|((location(s)?|spot(s)?|zone(s)?|area(s)?|space(s)?|lot(s)?|place(s)?|designation(s)?)\s+(for|where|allowed\s+for)\s+parking))\b",
    "additional private restrictions": r"\b(private|property)\b.*\b(restriction(s)?|rule(s)?|limitation(s)?)\b",
    "name of local authority": r"\b(local\s+(authority|municipality|council|city|town|region|office))\b",
    "direct link to authority": r"\b(contact|email|phone|reach|connect|website|office)\b.*\b(@|toronto\.ca|\.gov|\.ca|call)\b",
    "insurance requirements": r"\b(insurance|liability|coverage|policy|insured|certificate\s+of\s+insurance)\b",
    "physical requirements for trucks": r"\b(truck(s)?|vehicle(s)?)\b.*\b(requirement(s)?|must\s+have|equipment|dimension(s)?)\b",
    "exterior appearance guidelines": r"\b(exterior|appearance|design|look|paint|finish|signage|decoration)\b"
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
        for term, sentences in terms.items():
            for sentence in sentences:
                if score_categories(category, sentence):
                    score += 1
                    break
                else:
                    continue
                break
    score = (score / len(REGEX_PATTERNS)) * 100
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

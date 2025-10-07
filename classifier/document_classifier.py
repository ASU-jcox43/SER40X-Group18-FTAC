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
    # make the text lowercase to match our keywords
    # and keep track of the scores for each category
    lowercase = text.lower()
    scores = {}

    # for each category and keyword in our keywords list,
    # we count the number of matches we found looking through the text
    # if we don't find anything, we leave it blank (N/A) with a confidence of 0.0
    for category, keywords in KEYWORDS.items():
        count = sum(len(re.findall(rf'\b{term}\b', lowercase)) for term in keywords)
        scores[category] = count

    if not scores:
        return "N/A", 0.0

    # We pick the category in scores that has the highest number of matches,
    # and calculate our confidence rate based on the number of matches vs the total number of terms
    bestCategory = max(scores, key=scores.get)
    confidence = scores[bestCategory] / sum(scores.values())
    return bestCategory, round(confidence, 2)


def classify_files(folder_path):
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
    classify_files("test documents")

import os
import re
from collections import defaultdict


def accessDocuments(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            print(content)
            return content

    except FileNotFoundError:
        print(f"Error: File not found at {os.path.abspath(file_path)}")
    except Exception as e:
        print(f"An error occurred: {e}")


def cleanText(text):
    # Remove excessive whitespace and normalize to lowercase
    text = re.sub(r"\s+", " ", text.strip())
    text = text.lower()
    return text


def extractKeywords(text, keywords):
    keyword_context = defaultdict(list)
    for word in keywords:
        for match in re.finditer(word.lower(), text):
            start = max(match.start() - 50, 0)
            end = min(match.end() + 50, len(text))
            context = text[start:end]
            keyword_context[word].append(context)
    return dict(keyword_context)

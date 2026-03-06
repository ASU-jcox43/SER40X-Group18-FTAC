import re
from collections import defaultdict


def cleanText(text):
    # fix hyphenated line breaks
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
    # fix broken words across line breaks
    text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)
    # convert remaining newlines to space
    text = text.replace("\n", " ")
    # collapse whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip().lower()


def extractKeywords(text, keywords):
    keyword_context = defaultdict(list)

    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        sentence_lower = sentence.lower()

        for keyword in keywords:
            if keyword.lower() in sentence_lower:
                if keyword.lower() == "hours at any one time":
                    print(sentence)
                keyword_context[keyword].append(sentence.strip())

    return dict(keyword_context)

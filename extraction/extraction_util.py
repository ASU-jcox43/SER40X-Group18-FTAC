import re
from collections import defaultdict


def cleanText(text):
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"\n+", "\n", text)
    text = text.lower()
    return text


def extractKeywords(text, keywords):
    keyword_context = defaultdict(list)

    # Split into paragraphs using single newline (already collapsed)
    paragraphs = text.split("\n")

    for para in paragraphs:
        # Split paragraph into sentences using punctuation
        sentences = re.split(r"(?<=[.!?])\s+", para)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in keywords:
                if keyword.lower() in sentence_lower:
                    keyword_context[keyword].append(sentence.strip())

    return dict(keyword_context)

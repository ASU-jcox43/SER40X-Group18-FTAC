import re
import spacy
from collections import defaultdict

nlp = spacy.load("en_core_web_sm")

def splitSentences(text):
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'\n([a-z])', r' \1', text)
    text = re.sub(r'\n\s*(?:\d+\.|\(\w\)|•|-)\s+', '\n', text)
    text = re.sub(r';', '. ', text)
    doc = nlp(text)
    return [sent for sent in doc.sents if sent.text.strip()]


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
                keyword_context[keyword].append(sentence.strip())

    return dict(keyword_context)


def contextScore(text, weights):
    score = 0.0
    lower = text.lower()
    for keyword, weight in weights.items():
        if keyword in lower:
            score += weight
    return min(score, 1.0)


def extractMeaning(text):
    if any(x in text for x in ["shall not", "must not", "prohibited"]):
        return "prohibited"
    if any(x in text for x in ["shall", "must", "required"]):
        return "required"
    if any(x in text for x in ["may", "permitted"]):
        return "optional"
    return "unknown"


def negation(sentence):
    negations = {"except", "unless", "not applicable", "not required", "exempt", "exemption", "does not require"}
    lower = sentence.text.lower()
    for negation in negations:
        if negation in lower:
            return -0.3
    return 0.0


def modality(sentence):
    modals = {"shall", "must", "may"}
    for word in sentence:
        if word.text.lower() in modals:
            return 0.2
    return 0.0


def computeConfidence(sentence, weights, base=0.4):
    score = base
    score += contextScore(sentence.text, weights)
    score += modality(sentence)
    score += negation(sentence)
    return round(max(0, min(score, 1.0)), 2)
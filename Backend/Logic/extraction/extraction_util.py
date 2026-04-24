"""
Text Processing Utility Module

This module provides helper functions for:
- Cleaning raw text input
- Splitting text into sentences using spaCy
- Extracting keyword contexts
- Computing confidence scores for extracted rules
- Inferring meaning (required, prohibited, optional)

Dependencies:
- spaCy (NLP processing)
- Regular expressions (text normalization and matching)
"""

import re
import spacy
from collections import defaultdict

# Load spaCy English model for sentence parsing and NLP features
nlp = spacy.load("en_core_web_sm")


# TEXT PREPROCESSING

def splitSentences(text):
    """
    Splits input text into sentences using spaCy after preprocessing.

    Preprocessing steps:
    - Normalize newlines
    - Fix broken sentence formatting (e.g., list items, bullets)
    - Replace semicolons with sentence breaks

    Args:
        text (str): Raw input text

    Returns:
        List[Span]: List of spaCy sentence objects
    """
    # Normalize excessive newlines
    text = re.sub(r'\n+', '\n', text)

    # Fix lowercase continuation across line breaks
    text = re.sub(r'\n([a-z])', r' \1', text)

    # Remove bullet/list formatting
    text = re.sub(r'\n\s*(?:\d+\.|\(\w\)|•|-)\s+', '\n', text)

    # Convert semicolons into sentence separators
    text = re.sub(r';', '. ', text)

    # Process with spaCy
    doc = nlp(text)

    # Return non-empty sentences
    return [sent for sent in doc.sents if sent.text.strip()]


def cleanText(text):
    """
    Cleans raw text for processing.

    Steps:
    - Fix hyphenated line breaks
    - Repair broken words split across lines
    - Replace newlines with spaces
    - Normalize whitespace
    - Convert to lowercase

    Args:
        text (str): Raw text input

    Returns:
        str: Cleaned and normalized text
    """
    # Fix hyphenated line breaks (e.g., "exam-\nple" -> "example")
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)

    # Fix broken words across lines
    text = re.sub(r'(\w)\n(\w)', r'\1 \2', text)

    # Replace remaining newlines with spaces
    text = text.replace("\n", " ")

    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)

    return text.strip().lower()


# KEYWORD EXTRACTION

def extractKeywords(text, keywords):
    """
    Extracts sentences containing specified keywords.

    Args:
        text (str): Input text
        keywords (List[str]): Keywords to search for

    Returns:
        dict: Mapping of keyword -> list of matching sentences
    """
    keyword_context = defaultdict(list)

    # Split text into sentences using regex
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        sentence_lower = sentence.lower()

        for keyword in keywords:
            if keyword.lower() in sentence_lower:
                keyword_context[keyword].append(sentence.strip())

    return dict(keyword_context)


# SCORING & SEMANTIC ANALYSIS

def contextScore(text, weights):
    """
    Computes a weighted score based on keyword presence.

    Args:
        text (str): Input text
        weights (dict): Mapping of keyword -> weight

    Returns:
        float: Score capped at 1.0
    """
    score = 0.0
    lower = text.lower()

    for keyword, weight in weights.items():
        if keyword in lower:
            score += weight

    return min(score, 1.0)


def extractMeaning(text):
    """
    Infers the meaning of a sentence based on modal keywords.

    Categories:
    - prohibited
    - required
    - optional
    - unknown

    Args:
        text (str): Input text

    Returns:
        str: Meaning classification
    """
    if any(x in text for x in ["shall not", "must not", "prohibited"]):
        return "prohibited"

    if any(x in text for x in ["shall", "must", "required"]):
        return "required"

    if any(x in text for x in ["may", "permitted"]):
        return "optional"

    return "unknown"


def negation(sentence):
    """
    Detects negation or exception language in a sentence.

    Args:
        sentence (Span): spaCy sentence object

    Returns:
        float: Negative adjustment to confidence score
    """
    negations = {
        "except", "unless", "not applicable",
        "not required", "exempt", "exemption",
        "does not require"
    }

    lower = sentence.text.lower()

    for negation in negations:
        if negation in lower:
            return -0.3

    return 0.0


def modality(sentence):
    """
    Detects modal verbs that indicate requirement strength.

    Args:
        sentence (Span): spaCy sentence object

    Returns:
        float: Positive adjustment to confidence score
    """
    modals = {"shall", "must", "may"}

    for word in sentence:
        if word.text.lower() in modals:
            return 0.2

    return 0.0


def computeConfidence(sentence, weights, base=0.4):
    """
    Computes an overall confidence score for extracted information.

    Components:
    - Base score
    - Context keyword weighting
    - Modal strength
    - Negation penalty

    Args:
        sentence (Span): spaCy sentence object
        weights (dict): Keyword weight mapping
        base (float): Base confidence score

    Returns:
        float: Final confidence score (0.0 - 1.0)
    """
    score = base

    # Add weighted keyword context score
    score += contextScore(sentence.text, weights)

    # Add modal strength (shall, must, may)
    score += modality(sentence)

    # Subtract negation penalty if present
    score += negation(sentence)

    # Clamp score between 0 and 1
    return round(max(0, min(score, 1.0)), 2)
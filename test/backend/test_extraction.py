import spacy
import pytest

from Backend.Logic.extraction.extraction_util import (
    cleanText,
    extractKeywords,
    splitSentences
)

from Backend.Logic.extraction.text_extraction import (
    license_criteria,
    distance_criteria,
)

# Load NLP once for all tests
nlp = spacy.load("en_core_web_sm")


# TEXT CLEANING TESTS

def test_clean_text_basic():
    raw = "Hello\nWorld"
    assert cleanText(raw) == "hello world"


def test_clean_text_hyphen():
    raw = "exam-\nple"
    assert cleanText(raw) == "example"


# KEYWORD EXTRACTION TESTS

def test_extract_keywords():
    text = "A permit is required."
    keywords = ["permit"]

    result = extractKeywords(text, keywords)

    assert "permit" in result
    assert len(result["permit"]) == 1


def test_extract_multiple_keywords():
    text = "A permit is required. A license is needed."
    keywords = ["permit", "license"]

    result = extractKeywords(text, keywords)

    assert "permit" in result
    assert "license" in result


# CRITERIA FUNCTION TESTS

def test_license_required():
    text = "A business license is required before operating."
    sentence = list(nlp(text).sents)[0]

    result = license_criteria(sentence)

    assert result is not None
    assert result["criteria"] == "license_requirement"
    assert result["meaning"] == "required"


def test_license_optional():
    text = "A permit may be obtained."
    sentence = list(nlp(text).sents)[0]

    result = license_criteria(sentence)

    assert result is not None
    assert result["meaning"] == "optional"


def test_distance_rule():
    text = "Vendors must be at least 10 meters from restaurants."
    sentence = list(nlp(text).sents)[0]

    result = distance_criteria(sentence)

    assert result is not None
    assert result["criteria"] == "distance_restriction"
    assert result["distances"][0]["value"] == 10


# SENTENCE SPLITTING TEST

def test_split_sentences():
    text = "Hello world. This is a test."
    sentences = splitSentences(text)

    assert len(sentences) == 2
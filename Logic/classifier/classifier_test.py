"""
Test file for document classifier file.

Tests were made with pytest.
"""

import pytest
from document_classifier import classify_text

# Test to see if the document classifier correctly determines that text with the
# permit category terms is a permit document.
def test_permit_documents():
    """Check that permit documents are correctly classified."""
    example_text = "You require a permit for a food truck, as well as your food handlers license. " \
                   "You will also need to pass the truck inspection"

    category, confidence = classify_text(example_text)
    assert category == "Permit Documents"
    assert confidence > 0

# Test to see if the document classifier correctly determines that text with the
# legal category terms is a legal document.
def test_legal_documents():
    """Check that legal documents are correctly classified."""
    example_text = "This contract outlines the terms and conditions of the agreement." \
                   "The bylaw of this jurisdiction dictates the terms of this matter."
    category, confidence = classify_text(example_text)
    assert category == "Legal Documents"
    assert confidence > 0

# Test to see if the document classifier correctly determines that text with the
# financial category terms is a financial document.
def test_financial_documents():
    """Check that financial documents are correctly classified."""
    example_text = "Party A will send an invoice of $4000.00 USD to Party B for the vehicle." \
                   "The outlined taxes indicate the level of tax that a food truck owner must abide by."
    category, confidence = classify_text(example_text)
    assert category == "Financial Documents"
    assert confidence > 0

# Test to see if the document classifier correctly determines that text with the
# technical category terms is a technical document.
def test_technical_documents():
    """Check that technical documents are correctly classified."""
    example_text = "The following document contains the design for each food truck business." \
                   "The requirements state that a manual is to be given to each business owner prior to starting."
    category, confidence = classify_text(example_text)
    assert category == "Technical Documents"
    assert confidence > 0

# Test to see if the document classifier correctly determines that text with multiple
# category terms is a permit document.
def test_multiple_category_permit_documents():
    """Check that documents with multiple categories are correctly classified."""
    example_text = "If authorization is not given to an operating food vendor, a fee payment must be paid to the city." \
                   "The inspection must be passed or else the permit will be revoked due to the contract violation."
    category, confidence = classify_text(example_text)
    assert category == "Permit Documents"
    assert confidence > 0

# Test to see if the document classifier correctly determines that text with
# no category terms is an N/A document.
def test_NA_documents():
    """Check that documents with no category are correctly classified."""
    example_text = "SLJDKFJSDK FLJSDFLSKDFJSL DKFJSDKLFJSV XICHXIOEURPBXNN QWPEROV ZNLK"
    category, confidence = classify_text(example_text)
    assert category == "N/A"
    assert confidence == 0.0
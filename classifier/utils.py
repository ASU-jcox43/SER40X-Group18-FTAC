"""
Utility file for the document classifier.

This module supports text extraction for plain text, .docx (Microsoft Word) files, and PDF files
using the "extract text" function.

    Usage example:

    file_path = "test documents/example.docx"
    extract_text(file_path)
"""

from pathlib import Path
import PyPDF2
import docx


def extract_text(file_path: Path) -> str:
    """
    Extracts text from either a .txt, .pdf, or .docx file.

    Args:
       file_path: The path to the document.

    Returns:
         str: The extracted text from the document.
    """
    text = ""

    # Here we get either pdf, docx, or txt files and read them in accordingly,
    # then returns it without leading or trailing whitespaces with strip.
    if file_path.suffix.lower() == ".pdf":
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)

    elif file_path.suffix.lower() == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs)

    elif file_path.suffix.lower() == ".txt":
        text = file_path.read_text(encoding="utf-8", errors="ignore")

    else:
        text = ""

    return text.strip()

from pathlib import Path
import PyPDF2
import docx


def extract_text(file_path: Path) -> str:
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

# 🧠 OCR Processor

This project extracts and processes text from PDF files using **Optical Character Recognition (OCR)**.  
It supports both **scanned PDFs** (via Tesseract OCR) and **text-based PDFs** (via PyMuPDF).  
The output is organized into structured **JSON** files, separating text by sections.

---

## ⚙️ Setup Instructions

To run `OCRProcessor.py`, you'll need to install a few dependencies.  
Because these are in an **externally managed environment**, it’s recommended to use a **virtual environment**.

---

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 2. Install all dependencies from requirements text
```bash
pip install -r requirements.txt
```

### 5. Deactivate the virtual environment anytime using
```bash 
deactivate 
```

---
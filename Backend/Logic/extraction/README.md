# Text Extraction

## About
The text extraction module processes documents and web content to identify relevant information based on predefined keywords. It scans:

- Local files in Backend/test_documents
- URLs stored in the scrapy_config collection in MongoDB

For each document or webpage, the system:

- Cleans and processes the text
- Extracts keywords
- Identifies sentences containing those keywords
- Stores the extracted sentences in the extraction collection in MongoDB

## Supported Inputs

- .pdf files
- .txt files

Add additional documents into Backend/test_documents for processing

## Requirements

- MongoDB database
- Libraries
  - requests
  - bs4
  - PyPDF2

Run pip install for each library for use

```
pip install requests beautifulsoup4 PyPDF2
```

## Instructions

1. Navigate to root project directory:

```
cd SER40X-Group18-FTAC
```

2. Run text_extraction component

```
python -m Backend.Logic.extraction.text_extraction
```
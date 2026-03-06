# Bylaw Dashboard

A **municipality dashboard** for analyzing food truck friendliness scores across Canadian cities. Users can filter and sort municipalities, view detailed bylaw information, upload PDF bylaws for OCR processing, and download generated reports.

---

## Features

- **Dashboard** — filter municipalities by business type, province, and minimum friendliness score; sort results high to low or low to high; click any row to view a detailed breakdown
- **File Manager** — upload one or more PDF bylaw documents; run OCR individually or in bulk; view processing status live; completed files move to a separate section
- **OCR Pipeline** — uploaded PDFs are converted page-by-page and processed with Tesseract (English + French); extracted text saved as `.txt` alongside the PDF
- **Reports** — search and download generated reports
- **Active page indicator** — navigation highlights the current page

---

## Project Structure

```
dashboard/
├── index.html              # Main dashboard page
├── upload.html             # PDF upload & OCR page
├── generate_report.html    # Reports page
├── style.css               # Shared styles
├── script.js               # Shared dashboard logic
├── upload.js               # File Manager page logic
├── server.js               # Node/Express backend (upload + OCR pipeline)
├── package.json            # Node dependencies and scripts
├── uploads/                # Uploaded PDFs and OCR .txt output
├── testdata/               # Municipality JSON data files
│   └── index.json          # Index of municipality files
└── assets/                 # Logo and images
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `express` | Web server and routing |
| `multer` | PDF file upload handling |
| `tesseract.js` | OCR — text extraction from images (eng+fra) |
| `pdf-to-img` | PDF page → PNG image conversion (no system dependencies) |

**Requirements:** Node.js v18+ and npm.

---

## Setup & Running

1. Clone or download the project and navigate to the `dashboard/` folder:

```bash
cd path/to/dashboard
```

2. Install dependencies:

```bash
npm install
```

3. Start the server:

```bash
npm start
```

4. Open your browser to:

```
http://localhost:3000
```

> The project must be run via the Node server — opening HTML files directly as `file://` will not work due to `fetch()` calls for JSON data and the upload/OCR API.

---

## OCR Pipeline

PDFs uploaded through the File Manager page go through the following pipeline:

1. **Upload** — file saved to `uploads/`
2. **Convert** — each PDF page rendered to a PNG image (`pdf-to-img`)
3. **OCR** — Tesseract processes each page in English + French
4. **Output** — extracted text saved as `uploads/filename.txt`

OCR is triggered manually — files appear in the **Ready for OCR** queue after upload, and processing begins when the user clicks **Run OCR** (per file) or **Run OCR on All**.

---

## Browser Support

Chrome, Firefox, Edge (modern versions).
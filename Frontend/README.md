# Bylaw Dashboard

A **municipality dashboard** for analyzing food truck friendliness scores across Canadian cities. Users can filter and sort municipalities, view detailed bylaw information, upload PDF bylaws for OCR processing, and generate reports.

---

## Features

- **Dashboard** — filter municipalities by business type, province, and minimum friendliness score; sort results high to low or low to high; click any row to view a detailed breakdown
- **File Manager** — upload one or more PDF bylaw documents; run OCR individually or in bulk; view live processing status; view extracted OCR text inline; completed files move to a separate section
- **OCR Pipeline** — uploaded PDFs are converted page-by-page and processed with Tesseract (English + French); extracted text saved to `data/ocr_processed/` as `.txt` files; filenames are automatically sanitized on upload and server startup
- **Error Handling** — per-file error messages, retry support (up to 2 attempts), graceful page-level OCR failures, file size limits, and type validation
- **Reports** — search and download generated reports
- **Active page indicator** — navigation highlights the current page

---

## Project Structure

```
Frontend/
├── server.js                 # Node/Express backend (upload + OCR pipeline)
├── package.json              # Node dependencies and scripts
├── public/
│   ├── index.html            # Main dashboard page
│   ├── upload.html           # PDF upload & OCR page
│   ├── generate_report.html  # Reports page
│   ├── scrapy_config.html    # Scraping config page
│   ├── css/
│   │   ├── style.css
│   │   └── scrapy_style.css
│   ├── js/
│   │   ├── script.js
│   │   ├── upload.js
│   │   ├── reportpost.js
│   │   └── scrapy_config.js
│   ├── assets/
│   │   └── ftacLogo.png
│   └── testdata/
│       └── index.json
└── data/
    ├── uploads/              # Uploaded PDFs
    └── ocr_processed/        # OCR extracted .txt output files
```

> Both `data/uploads/` and `data/ocr_processed/` are created automatically when the server starts if they don't exist.

---

## Dependencies

| Package | Purpose |
|---|---|
| `express` | Web server and routing |
| `multer` | PDF file upload handling with size and type validation |
| `tesseract.js` | OCR — text extraction from page images (eng+fra) |
| `pdf-to-img` | PDF page → PNG image conversion (no system dependencies required) |

**Requirements:** Node.js v18+ and npm.

> No system-level libraries (Cairo, GraphicsMagick, Poppler, etc.) are required. All dependencies are pure Node or self-contained.

---

## Setup & Running

1. Clone or download the project and navigate to the `Frontend/` folder:

```bash
cd path/to/Frontend
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

1. **Upload** — PDF saved to `data/uploads/`, filename sanitized automatically
2. **Convert** — each PDF page rendered to a PNG image via `pdf-to-img`
3. **OCR** — Tesseract processes each page in English + French; individual page failures are skipped rather than aborting the job
4. **Output** — extracted text saved to `data/ocr_processed/filename.txt`
5. **View** — completed files show a **View** button that opens the raw OCR text in a modal

OCR is triggered manually — files appear in the **Ready for OCR** queue after upload, and processing begins when the user clicks **Run OCR** (per file) or **Run OCR on All**.

### Full proposed pipeline (in progress)

```
PDF (image or text)
       ↓
   pdf-to-img          ← converts pages to PNG
       ↓
  Tesseract OCR        ← eng+fra, page by page
       ↓
  ocr_processed/
  filename.txt         ← saved automatically  ✅ implemented
       ↓
  Claude API           ← structured extraction (triggered separately)
       ↓
  ocr_processed/
  filename.json        ← municipality data in structured format  🔲 todo
       ↓
  Report generator     ← reads .json, builds PDF or Word report  🔲 todo
```

---

## Browser Support

Chrome, Firefox, Edge (modern versions).

---

## Todo / Future Tasks

### Backend

- [ ] **`POST /extract/:jobId`** — add a Claude API extraction endpoint that reads an existing `.txt` from `ocr_processed/` and returns structured JSON using the municipality schema (permit cost, zones, operating hours, insurance requirements, etc.)
- [ ] **Save `.json` to `ocr_processed/`** — store Claude's structured output alongside the `.txt` and `.pdf` for use by the report generator
- [ ] **`GET /files` enhancement** — return `hasTxt` and `hasJson` flags per file so the frontend can show which stage each document is at
- [ ] **Job persistence** — currently jobs are stored in memory and lost on server restart; persist job state to a JSON file or SQLite database
- [ ] **Duplicate file handling** — detect and warn when a file with the same name already exists in `uploads/` before overwriting

### Frontend — File Manager (`upload.html`)

- [ ] **"Extract → JSON" button** — appears on completed OCR files; triggers `POST /extract/:jobId` and polls for completion
- [ ] **View JSON button** — similar to the existing View (txt) button; opens structured JSON in a modal once extraction is complete
- [ ] **Pipeline stage indicator** — show which stage each file is at (Uploaded / OCR Done / JSON Ready) as a visual step tracker rather than just a badge
- [ ] **Persist queue across page refresh** — re-load completed files from `GET /files` on page load so the completed list survives navigation

### Frontend — Reports (`generate_report.html`)

- [ ] **Connect to `ocr_processed/*.json`** — replace or supplement static `testdata/` with live extracted municipality data
- [ ] **Single municipality report** — generate a formatted PDF or Word document for one municipality using its `.json` data
- [ ] **Comparison report** — side-by-side view and downloadable report across multiple selected municipalities
- [ ] **Browser preview** — render the report as HTML in-page before downloading as PDF or `.docx`
- [ ] **CSV / Excel export** — export the structured JSON data from multiple municipalities into a spreadsheet

### Infrastructure

- [ ] **Claude API integration** — add `@anthropic-ai/sdk`, implement the extraction prompt for bilingual bylaw text, handle token limits for long documents by chunking
- [ ] **Environment config** — move `PORT`, `MAX_FILE_SIZE_MB`, `MAX_RETRIES`, and `ANTHROPIC_API_KEY` into a `.env` file using `dotenv`
- [ ] **`.gitignore`** — ensure `uploads/`, `ocr_processed/`, `node_modules/`, and `.env` are excluded from version control
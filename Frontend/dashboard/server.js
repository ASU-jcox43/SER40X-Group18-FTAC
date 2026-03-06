/* ══════════════════════════════════════════════════════════════
   server.js
   Pipeline: PDF upload → (manual trigger) → Tesseract OCR
             (eng+fra) → raw text saved to uploads/filename.txt

   Install dependencies:
     npm install express multer tesseract.js pdf-to-img

   Then run:
     node server.js
══════════════════════════════════════════════════════════════ */

const express   = require('express');
const multer    = require('multer');
const path      = require('path');
const fs        = require('fs');
const os        = require('os');
const Tesseract = require('tesseract.js');

const app  = express();
const PORT = 3000;

/* ── Directory setup ──────────────────────────────────────────── */
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir);

/* ── In-memory job store ──────────────────────────────────────── */
// jobId → { id, filename, stage, progress, error, result }
// stages: 'ready' | 'ocr' | 'done' | 'failed'
const jobStore = {};

function createJob(filename) {
  const id  = `job-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
  const job = { id, filename, stage: 'ready', progress: 0, error: null, result: null };
  jobStore[id] = job;
  return job;
}

function setStage(job, stage, progress = 0) {
  job.stage    = stage;
  job.progress = progress;
  console.log(`[${job.id}] ${stage} — ${progress}%`);
}

/* ── Multer — save PDFs to uploads/ ──────────────────────────── */
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename:    (req, file, cb) => cb(null, file.originalname),
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    file.mimetype === 'application/pdf'
      ? cb(null, true)
      : cb(new Error('Only PDF files are allowed'), false);
  },
});

/* ── Static files ─────────────────────────────────────────────── */
app.use(express.static(__dirname));
app.use(express.json());

/* ════════════════════════════════════════════════════════════════
   POST /upload
   Saves PDF, creates job in 'ready' state, returns jobId.
   OCR does NOT start yet — waits for POST /ocr/:jobId.
════════════════════════════════════════════════════════════════ */
app.post('/upload', upload.single('pdfFile'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file received' });
  }

  const job = createJob(req.file.filename);
  console.log(`[${job.id}] Uploaded — ${job.filename} (awaiting OCR trigger)`);

  res.json({ message: 'Upload successful', filename: req.file.filename, jobId: job.id });
});

/* ════════════════════════════════════════════════════════════════
   POST /ocr/:jobId
   Manually triggers OCR for a specific job.
   Returns immediately; client polls GET /job/:jobId for progress.
════════════════════════════════════════════════════════════════ */
app.post('/ocr/:jobId', (req, res) => {
  const job = jobStore[req.params.jobId];

  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }
  if (job.stage === 'ocr') {
    return res.status(409).json({ error: 'OCR already in progress for this job' });
  }
  if (job.stage === 'done') {
    return res.status(409).json({ error: 'OCR already completed for this job' });
  }

  res.json({ message: 'OCR started', jobId: job.id });

  // Run OCR in background
  runPipeline(job, path.join(uploadsDir, job.filename)).catch(err => {
    console.error(`[${job.id}] Unhandled OCR error:`, err);
    job.stage = 'failed';
    job.error = err.message;
  });
});

/* ════════════════════════════════════════════════════════════════
   GET /job/:id
   Frontend polls this for live stage + progress
════════════════════════════════════════════════════════════════ */
app.get('/job/:id', (req, res) => {
  const job = jobStore[req.params.id];
  if (!job) return res.status(404).json({ error: 'Job not found' });
  res.json({
    id:       job.id,
    filename: job.filename,
    stage:    job.stage,
    progress: job.progress,
    error:    job.error,
    result:   job.result,
  });
});

/* ════════════════════════════════════════════════════════════════
   GET /files
   Returns list of PDFs in uploads/ with .txt result flag
════════════════════════════════════════════════════════════════ */
app.get('/files', (req, res) => {
  const pdfs  = fs.readdirSync(uploadsDir).filter(f => f.endsWith('.pdf'));
  const files = pdfs.map(pdf => ({
    filename:  pdf,
    hasResult: fs.existsSync(path.join(uploadsDir, pdf.replace('.pdf', '.txt'))),
  }));
  res.json(files);
});

/* ════════════════════════════════════════════════════════════════
   PIPELINE — PDF → images → Tesseract (eng+fra) → .txt
   Uses pdf-to-img (no system dependencies required)
════════════════════════════════════════════════════════════════ */
async function runPipeline(job, pdfPath) {
  setStage(job, 'ocr', 0);

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ocr-'));

  try {
    // pdf-to-img is an ES module — must use dynamic import
    const { pdf } = await import('pdf-to-img');

    const doc        = await pdf(pdfPath, { scale: 2 });
    const total      = doc.length;
    const imageFiles = [];

    // Render each page and save as PNG
    let pageNum = 1;
    for await (const image of doc) {
      const imgPath = path.join(tmpDir, `page-${String(pageNum).padStart(4, '0')}.png`);
      fs.writeFileSync(imgPath, image);
      imageFiles.push(imgPath);
      pageNum++;
    }

    if (imageFiles.length === 0) {
      throw new Error('PDF has no pages — may be encrypted or corrupt.');
    }

    // OCR each page with Tesseract (English + French)
    let fullText = '';

    for (let i = 0; i < total; i++) {
      const { data: { text } } = await Tesseract.recognize(imageFiles[i], 'eng+fra', {
        logger: m => {
          if (m.status === 'recognizing text') {
            const pageBase  = (i / total) * 100;
            const pageSlice = (1 / total) * 100;
            job.progress    = Math.round(pageBase + m.progress * pageSlice);
          }
        },
      });
      fullText += `\n--- Page ${i + 1} ---\n${text}`;
    }

    // Save OCR output as .txt next to the PDF
    const txtPath = path.join(uploadsDir, job.filename.replace('.pdf', '.txt'));
    fs.writeFileSync(txtPath, fullText.trim(), 'utf8');

    job.result   = { savedTo: path.basename(txtPath), pageCount: total };
    job.progress = 100;
    setStage(job, 'done', 100);
    console.log(`[${job.id}] ✅ Done — saved ${path.basename(txtPath)}`);

  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

/* ── Start ────────────────────────────────────────────────────── */
app.listen(PORT, () => {
  console.log(`\nServer running at http://localhost:${PORT}`);
  console.log(`Open:  http://localhost:${PORT}/upload.html\n`);
});
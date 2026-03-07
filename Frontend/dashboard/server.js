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
if (!fs.existsSync(uploadsDir)) fs.mkdirSync(uploadsDir, { recursive: true });

/* ── In-memory job store ──────────────────────────────────────── */
// jobId → { id, filename, stage, progress, error, result, retryCount }
// stages: 'ready' | 'ocr' | 'done' | 'failed'
const jobStore  = {};
const MAX_RETRIES = 2;
const MAX_FILE_SIZE_MB = 50;

function createJob(filename) {
  const id  = `job-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
  const job = {
    id,
    filename,
    stage:      'ready',
    progress:   0,
    error:      null,
    result:     null,
    retryCount: 0,
  };
  jobStore[id] = job;
  return job;
}

function setStage(job, stage, progress = 0) {
  job.stage    = stage;
  job.progress = progress;
  console.log(`[${job.id}] ${stage} — ${progress}%`);
}

function failJob(job, message, err = null) {
  job.stage    = 'failed';
  job.progress = 0;
  job.error    = message;
  if (err) console.error(`[${job.id}] ❌ ${message}`, err);
  else     console.error(`[${job.id}] ❌ ${message}`);
}

/* ── Multer — save PDFs to uploads/ ──────────────────────────── */
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename:    (req, file, cb) => cb(null, file.originalname),
});

const upload = multer({
  storage,
  limits: { fileSize: MAX_FILE_SIZE_MB * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error(`Only PDF files are accepted (received: ${file.mimetype})`), false);
    }
  },
});

/* ── Multer error handler ─────────────────────────────────────── */
function handleUpload(req, res, next) {
  upload.single('pdfFile')(req, res, err => {
    if (!err) return next();

    if (err.code === 'LIMIT_FILE_SIZE') {
      return res.status(413).json({
        error: `File too large — maximum size is ${MAX_FILE_SIZE_MB}MB.`,
      });
    }
    if (err.message?.startsWith('Only PDF')) {
      return res.status(415).json({ error: err.message });
    }
    // Disk write errors or other multer failures
    console.error('[upload] Multer error:', err);
    return res.status(500).json({ error: 'File could not be saved. Check disk space.' });
  });
}

/* ── Static files ─────────────────────────────────────────────── */
app.use(express.static(__dirname));
app.use(express.json());

/* ════════════════════════════════════════════════════════════════
   POST /upload  (#223)
   Validates, saves PDF, creates job. Returns jobId.
   Errors: no file, wrong type, too large, disk failure.
════════════════════════════════════════════════════════════════ */
app.post('/upload', handleUpload, (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file received.' });
  }

  // Guard: reject empty files that slipped through
  if (req.file.size === 0) {
    fs.unlink(req.file.path, () => {});
    return res.status(400).json({ error: 'Uploaded file is empty.' });
  }

  const job = createJob(req.file.filename);
  console.log(`[${job.id}] Uploaded — ${job.filename} (awaiting OCR trigger)`);
  res.json({ message: 'Upload successful', filename: req.file.filename, jobId: job.id });
});

/* ════════════════════════════════════════════════════════════════
   POST /ocr/:jobId  (#223)
   Triggers OCR for a job. Supports retry if previously failed.
   Errors: job not found, already running, already done.
════════════════════════════════════════════════════════════════ */
app.post('/ocr/:jobId', (req, res) => {
  const job = jobStore[req.params.jobId];

  if (!job) {
    return res.status(404).json({ error: 'Job not found. It may have expired — please re-upload.' });
  }
  if (job.stage === 'ocr') {
    return res.status(409).json({ error: 'OCR is already running for this file.' });
  }
  if (job.stage === 'done') {
    return res.status(409).json({ error: 'OCR already completed for this file.' });
  }

  // Allow retry if previously failed
  if (job.stage === 'failed') {
    if (job.retryCount >= MAX_RETRIES) {
      return res.status(429).json({
        error: `OCR failed after ${MAX_RETRIES} attempts. Please re-upload the file.`,
      });
    }
    job.retryCount++;
    job.error = null;
    console.log(`[${job.id}] Retrying OCR (attempt ${job.retryCount}/${MAX_RETRIES})`);
  }

  // Guard: verify the PDF still exists on disk
  const pdfPath = path.join(uploadsDir, job.filename);
  if (!fs.existsSync(pdfPath)) {
    return res.status(404).json({
      error: 'PDF file not found on disk. Please re-upload the file.',
    });
  }

  res.json({ message: 'OCR started', jobId: job.id });

  runPipeline(job, pdfPath).catch(err => {
    failJob(job, `Unexpected pipeline error: ${err.message}`, err);
  });
});

/* ════════════════════════════════════════════════════════════════
   GET /job/:id
   Frontend polls this for live stage, progress, and error details.
════════════════════════════════════════════════════════════════ */
app.get('/job/:id', (req, res) => {
  const job = jobStore[req.params.id];
  if (!job) return res.status(404).json({ error: 'Job not found.' });
  res.json({
    id:         job.id,
    filename:   job.filename,
    stage:      job.stage,
    progress:   job.progress,
    error:      job.error,
    result:     job.result,
    retryCount: job.retryCount,
    canRetry:   job.stage === 'failed' && job.retryCount < MAX_RETRIES,
  });
});

/* ════════════════════════════════════════════════════════════════
   GET /ocr-result/:filename  (#222)
   Returns raw OCR text for a completed file.
   Frontend uses this to populate the View modal.
════════════════════════════════════════════════════════════════ */
app.get('/ocr-result/:filename', (req, res) => {
  const filename = path.basename(req.params.filename); // strip any path traversal
  if (!filename.endsWith('.txt')) {
    return res.status(400).json({ error: 'Only .txt files can be retrieved.' });
  }

  const txtPath = path.join(uploadsDir, filename);
  if (!fs.existsSync(txtPath)) {
    return res.status(404).json({ error: 'OCR result not found. Has OCR been run for this file?' });
  }

  try {
    const text = fs.readFileSync(txtPath, 'utf8');
    res.type('text/plain').send(text);
  } catch (err) {
    console.error(`[/ocr-result] Failed to read ${filename}:`, err);
    res.status(500).json({ error: 'Could not read OCR result file.' });
  }
});

/* ════════════════════════════════════════════════════════════════
   GET /files
   Returns list of PDFs in uploads/ with .txt result flag.
════════════════════════════════════════════════════════════════ */
app.get('/files', (req, res) => {
  try {
    const pdfs  = fs.readdirSync(uploadsDir).filter(f => f.endsWith('.pdf'));
    const files = pdfs.map(pdf => ({
      filename:  pdf,
      hasResult: fs.existsSync(path.join(uploadsDir, pdf.replace('.pdf', '.txt'))),
    }));
    res.json(files);
  } catch (err) {
    console.error('[/files] Error reading uploads dir:', err);
    res.status(500).json({ error: 'Could not read uploads directory.' });
  }
});

/* ════════════════════════════════════════════════════════════════
   PIPELINE — PDF → images → Tesseract (eng+fra) → .txt  (#223)

   Error handling:
   - pdf-to-img failure (encrypted, corrupt, unsupported)
   - Empty PDF (0 pages)
   - Tesseract failure on individual pages (skipped, not fatal)
   - Complete Tesseract failure (all pages failed)
   - .txt write failure (disk full, permissions)
   - Temp dir always cleaned up in finally block
════════════════════════════════════════════════════════════════ */
async function runPipeline(job, pdfPath) {
  setStage(job, 'ocr', 0);

  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'ocr-'));

  try {
    /* ── Stage 1: PDF → PNG images ──────────────────────────────── */
    let pdfModule;
    try {
      pdfModule = await import('pdf-to-img');
    } catch (err) {
      throw new Error('pdf-to-img module could not be loaded. Run: npm install pdf-to-img');
    }

    let doc;
    try {
      doc = await pdfModule.pdf(pdfPath, { scale: 2 });
    } catch (err) {
      throw new Error(
        `Could not open PDF — it may be password-protected, corrupt, or an unsupported format. (${err.message})`
      );
    }

    const total      = doc.length;
    const imageFiles = [];

    if (total === 0) {
      throw new Error('PDF contains no pages.');
    }

    let pageNum = 1;
    for await (const image of doc) {
      const imgPath = path.join(tmpDir, `page-${String(pageNum).padStart(4, '0')}.png`);
      try {
        fs.writeFileSync(imgPath, image);
        imageFiles.push(imgPath);
      } catch (err) {
        // Skip pages that fail to render rather than aborting entirely
        console.warn(`[${job.id}] Page ${pageNum} failed to render — skipping. (${err.message})`);
      }
      pageNum++;
    }

    if (imageFiles.length === 0) {
      throw new Error('No pages could be rendered from this PDF.');
    }

    /* ── Stage 2: Tesseract OCR per page ────────────────────────── */
    let fullText     = '';
    let failedPages  = [];
    const rendered   = imageFiles.length;

    for (let i = 0; i < rendered; i++) {
      try {
        const { data: { text } } = await Tesseract.recognize(imageFiles[i], 'eng+fra', {
          logger: m => {
            if (m.status === 'recognizing text') {
              const pageBase  = (i / rendered) * 100;
              const pageSlice = (1 / rendered) * 100;
              job.progress    = Math.round(pageBase + m.progress * pageSlice);
            }
          },
        });
        fullText += `\n--- Page ${i + 1} ---\n${text}`;
      } catch (err) {
        // Individual page failure — log and continue
        console.warn(`[${job.id}] OCR failed on page ${i + 1} — skipping. (${err.message})`);
        failedPages.push(i + 1);
        fullText += `\n--- Page ${i + 1} ---\n[OCR failed for this page]\n`;
      }
    }

    // If every single page failed, treat as a full failure
    if (failedPages.length === rendered) {
      throw new Error('OCR failed on all pages. The PDF may contain only images or be unreadable.');
    }

    /* ── Stage 3: Save .txt output ──────────────────────────────── */
    const txtPath = path.join(uploadsDir, job.filename.replace('.pdf', '.txt'));
    try {
      fs.writeFileSync(txtPath, fullText.trim(), 'utf8');
    } catch (err) {
      throw new Error(`Could not save OCR output — check disk space or permissions. (${err.message})`);
    }

    // Note partial failures in result but still mark done
    const warnings = failedPages.length > 0
      ? `Pages with OCR errors: ${failedPages.join(', ')}`
      : null;

    job.result   = { savedTo: path.basename(txtPath), pageCount: total, warnings };
    job.progress = 100;
    setStage(job, 'done', 100);

    if (warnings) {
      console.warn(`[${job.id}] ⚠️  Done with warnings — ${warnings}`);
    } else {
      console.log(`[${job.id}] ✅ Done — saved ${path.basename(txtPath)}`);
    }

  } catch (err) {
    failJob(job, err.message, err);
  } finally {
    // Always clean up temp images, even on failure
    try {
      fs.rmSync(tmpDir, { recursive: true, force: true });
    } catch (cleanupErr) {
      console.warn(`[${job.id}] Could not clean up temp dir ${tmpDir}:`, cleanupErr.message);
    }
  }
}

/* ── Start ────────────────────────────────────────────────────── */
app.listen(PORT, () => {
  console.log(`\nServer running at http://localhost:${PORT}`);
  console.log(`Open:  http://localhost:${PORT}/upload.html\n`);
});
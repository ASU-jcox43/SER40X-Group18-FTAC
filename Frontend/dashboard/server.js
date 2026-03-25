/* ══════════════════════════════════════════════════════════════
   server.js
   Pipeline: PDF upload → (manual trigger) → Tesseract OCR
             (eng+fra) → raw text saved to ocr_processed/filename.txt

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
const uploadsDir    = path.join(__dirname, 'uploads');
const ocrOutputDir  = path.join(__dirname, 'ocr_processed');

if (!fs.existsSync(uploadsDir))   fs.mkdirSync(uploadsDir,   { recursive: true });
if (!fs.existsSync(ocrOutputDir)) fs.mkdirSync(ocrOutputDir, { recursive: true });

/* ── Sanitize any existing dirty filenames on startup ─────────── */
function migrateDirFilenames(dir, ext) {
  fs.readdirSync(dir)
    .filter(f => f.endsWith(ext))
    .forEach(f => {
      const clean = sanitizeFilename(f);
      if (clean !== f) {
        const oldPath = path.join(dir, f);
        const newPath = path.join(dir, clean);
        if (!fs.existsSync(newPath)) {
          fs.renameSync(oldPath, newPath);
          console.log(`[startup] Renamed: "${f}" → "${clean}"`);
        }
      }
    });
}

migrateDirFilenames(uploadsDir,   '.pdf');
migrateDirFilenames(ocrOutputDir, '.txt');

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

/* ── Filename sanitizer ───────────────────────────────────────── */
function sanitizeFilename(name) {
  return name
    .normalize('NFD')                    // decompose accented chars
    .replace(/[\u0300-\u036f]/g, '')     // strip accent marks
    .replace(/[–—]/g, '-')              // em/en dash → hyphen
    .replace(/[^\w.\-]/g, '-')          // anything else non-safe → hyphen
    .replace(/-+/g, '-')                // collapse multiple hyphens
    .replace(/^-|-$/g, '');             // trim leading/trailing hyphens
}

/* ── Multer — save PDFs to uploads/ ──────────────────────────── */
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename: (req, file, cb) => cb(null, sanitizeFilename(file.originalname)),
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
   GET /ocr-result/:filename  
   Returns raw OCR text for a completed file.
   Frontend uses this to populate the View modal and Download.
════════════════════════════════════════════════════════════════ */
app.get('/ocr-result/:filename', (req, res) => {
  const filename = path.basename(req.params.filename); // strip any path traversal
  if (!filename.endsWith('.txt')) {
    return res.status(400).json({ error: 'Only .txt files can be retrieved.' });
  }

  const txtPath = path.join(ocrOutputDir, filename);
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
      hasResult: fs.existsSync(path.join(ocrOutputDir, pdf.replace('.pdf', '.txt'))),
    }));
    res.json(files);
  } catch (err) {
    console.error('[/files] Error reading uploads dir:', err);
    res.status(500).json({ error: 'Could not read uploads directory.' });
  }
});

/* ════════════════════════════════════════════════════════════════
   SSE CLIENT REGISTRY
   Keeps track of open SSE connections so we can push events to
   all connected browser tabs when a new file is processed.
════════════════════════════════════════════════════════════════ */
const sseClients = new Set();

function broadcastProcessedFile(entry) {
  const payload = `event: processed-file\ndata: ${JSON.stringify(entry)}\n\n`;
  for (const res of sseClients) {
    try { res.write(payload); } catch (_) { sseClients.delete(res); }
  }
}

/* ════════════════════════════════════════════════════════════════
   GET /processed-files  
   Returns all .txt files in ocr_processed/ as a JSON array.
   Each entry: { pdfName, txtFilename, processedAt }
   Frontend calls this once on page load to populate the
   persistent Completed PDFs list.
════════════════════════════════════════════════════════════════ */
app.get('/processed-files', (req, res) => {
  try {
    const txts = fs.readdirSync(ocrOutputDir).filter(f => f.endsWith('.txt'));

    const files = txts.map(txt => {
      const fullPath    = path.join(ocrOutputDir, txt);
      const stats       = fs.statSync(fullPath);
      const pdfName     = txt.replace(/\.txt$/, '.pdf');
      return {
        pdfName,
        txtFilename:  txt,
        processedAt:  stats.mtime.toISOString(),
      };
    });

    // Sort newest first
    files.sort((a, b) => new Date(b.processedAt) - new Date(a.processedAt));

    res.json(files);
  } catch (err) {
    console.error('[/processed-files] Error reading ocr_processed dir:', err);
    res.status(500).json({ error: 'Could not read processed files directory.' });
  }
});

/* ════════════════════════════════════════════════════════════════
   GET /processed-files/stream  (#259)
   Server-Sent Events endpoint. Stays open and pushes a
   'processed-file' event whenever a new OCR result is saved.
   The frontend's EventSource reconnects automatically on drop.
════════════════════════════════════════════════════════════════ */
app.get('/processed-files/stream', (req, res) => {
  res.setHeader('Content-Type',  'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection',    'keep-alive');
  res.flushHeaders();

  // Keep connection alive with a comment ping every 25s
  const heartbeat = setInterval(() => {
    try { res.write(': ping\n\n'); } catch (_) { clearInterval(heartbeat); }
  }, 25_000);

  sseClients.add(res);
  console.log(`[SSE] Client connected (${sseClients.size} total)`);

  req.on('close', () => {
    clearInterval(heartbeat);
    sseClients.delete(res);
    console.log(`[SSE] Client disconnected (${sseClients.size} remaining)`);
  });
});

/* ════════════════════════════════════════════════════════════════
   DELETE /processed-files/:filename  
   Deletes a .txt file from ocr_processed/.
   Frontend calls this when the user clicks Delete on a row.
════════════════════════════════════════════════════════════════ */
app.delete('/processed-files/:filename', (req, res) => {
  const filename = path.basename(req.params.filename);

  if (!filename.endsWith('.txt')) {
    return res.status(400).json({ error: 'Only .txt files can be deleted via this endpoint.' });
  }

  const txtPath = path.join(ocrOutputDir, filename);
  if (!fs.existsSync(txtPath)) {
    return res.status(404).json({ error: 'File not found.' });
  }

  try {
    fs.unlinkSync(txtPath);
    console.log(`[DELETE /processed-files] Deleted: ${filename}`);
    res.json({ message: 'Deleted successfully.', filename });
  } catch (err) {
    console.error(`[DELETE /processed-files] Failed to delete ${filename}:`, err);
    res.status(500).json({ error: 'Could not delete file. Check permissions.' });
  }
});

/* ════════════════════════════════════════════════════════════════
   POST /rerun/:txtFilename 
   Re-queues the original PDF for OCR when the user clicks
   "Re-run OCR" on a completed row.
   - Derives the PDF name from the .txt filename
   - Verifies the original PDF still exists in uploads/
   - Creates a fresh job and kicks off the pipeline
   - Returns { jobId } so the frontend can poll progress
   - Broadcasts the new result via SSE when done
════════════════════════════════════════════════════════════════ */
app.post('/rerun/:txtFilename', (req, res) => {
  const txtFilename = path.basename(req.params.txtFilename);

  if (!txtFilename.endsWith('.txt')) {
    return res.status(400).json({ error: 'Expected a .txt filename.' });
  }

  const pdfFilename = txtFilename.replace(/\.txt$/, '.pdf');
  const pdfPath     = path.join(uploadsDir, pdfFilename);

  if (!fs.existsSync(pdfPath)) {
    return res.status(404).json({
      error: `Original PDF "${pdfFilename}" not found in uploads. Please re-upload the file.`,
    });
  }

  // Remove the old .txt so the pipeline can overwrite cleanly
  const oldTxtPath = path.join(ocrOutputDir, txtFilename);
  if (fs.existsSync(oldTxtPath)) {
    try { fs.unlinkSync(oldTxtPath); } catch (_) {}
  }

  const job = createJob(pdfFilename);
  console.log(`[${job.id}] Re-run OCR requested for ${pdfFilename}`);

  res.json({ jobId: job.id, pdfName: pdfFilename });

  runPipeline(job, pdfPath).catch(err => {
    failJob(job, `Unexpected pipeline error: ${err.message}`, err);
  });
});

/* ════════════════════════════════════════════════════════════════
   PIPELINE — PDF → images → Tesseract (eng+fra) → .txt  
   On success, broadcasts the new file to all SSE clients 
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
        console.warn(`[${job.id}] OCR failed on page ${i + 1} — skipping. (${err.message})`);
        failedPages.push(i + 1);
        fullText += `\n--- Page ${i + 1} ---\n[OCR failed for this page]\n`;
      }
    }

    if (failedPages.length === rendered) {
      throw new Error('OCR failed on all pages. The PDF may contain only images or be unreadable.');
    }

    /* ── Stage 3: Save .txt output ──────────────────────────────── */
    const txtFilename = job.filename.replace('.pdf', '.txt');
    const txtPath     = path.join(ocrOutputDir, txtFilename);
    try {
      fs.writeFileSync(txtPath, fullText.trim(), 'utf8');
    } catch (err) {
      throw new Error(`Could not save OCR output — check disk space or permissions. (${err.message})`);
    }

    const warnings = failedPages.length > 0
      ? `Pages with OCR errors: ${failedPages.join(', ')}`
      : null;

    job.result   = { savedTo: txtFilename, pageCount: total, warnings };
    job.progress = 100;
    setStage(job, 'done', 100);

    if (warnings) {
      console.warn(`[${job.id}] ⚠️  Done with warnings — ${warnings}`);
    } else {
      console.log(`[${job.id}] ✅ Done — saved ${txtFilename}`);
    }

    /* Notify SSE clients of the new completed file */
    const stats = fs.statSync(txtPath);
    broadcastProcessedFile({
      pdfName:     job.filename,
      txtFilename,
      processedAt: stats.mtime.toISOString(),
    });

  } catch (err) {
    failJob(job, err.message, err);
  } finally {
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
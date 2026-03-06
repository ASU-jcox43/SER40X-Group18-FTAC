const express = require('express');
const multer  = require('multer');
const path    = require('path');
const fs      = require('fs');

const app  = express();
const PORT = 3000;

// ── Ensure uploads/ folder exists ─────────────────────────────
const uploadsDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir);
}

// ── Multer — save files to uploads/, keep original filename ───
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadsDir),
  filename:    (req, file, cb) => cb(null, file.originalname),
});

const upload = multer({
  storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/pdf') {
      cb(null, true);
    } else {
      cb(new Error('Only PDF files are allowed'), false);
    }
  },
});

// ── Serve all static files (HTML, CSS, JS) ────────────────────
app.use(express.static(__dirname));

// ── POST /upload — receives PDF and saves to uploads/ ─────────
app.post('/upload', upload.single('pdfFile'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file received' });
  }
  res.json({ message: 'Upload successful', filename: req.file.filename });
});

// ── GET /files — returns list of files in uploads/ ────────────
app.get('/files', (req, res) => {
  const files = fs.readdirSync(uploadsDir).filter(f => f.endsWith('.pdf'));
  res.json(files);
});

// ── Start ──────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
  console.log(`Open http://localhost:${PORT}/upload.html`);
});
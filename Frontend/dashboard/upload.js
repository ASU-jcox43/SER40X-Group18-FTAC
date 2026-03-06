/* ── Element refs ─────────────────────────────────────────────── */
const dropArea      = document.getElementById('dropArea');
const pdfInput      = document.getElementById('pdfInput');
const uploadBtn     = document.getElementById('uploadBtn');
const fileNameEl    = document.getElementById('fileName');
const statusEl      = document.getElementById('status');
const progressCont  = document.getElementById('progressContainer');
const progressBar   = document.getElementById('progressBar');
const uploadedFiles = document.getElementById('uploadedFiles');
const statusJobList = document.getElementById('statusJobList');
const statusEmpty   = document.getElementById('statusEmpty');
const liveIndicator = document.getElementById('liveIndicator');

/* ── Job state ────────────────────────────────────────────────── */
const jobs = {}; // jobId → { id, name, status, progress, fileListEl, statusPanelEl }

/* ── Status metadata ──────────────────────────────────────────── */
const STATUS_META = {
  uploading:  { label: 'Uploading',      badgeClass: 'badge-uploading',  spinner: true,  icon: null },
  processing: { label: 'OCR Processing', badgeClass: 'badge-processing', spinner: true,  icon: null },
  complete:   { label: 'Complete',       badgeClass: 'badge-complete',   spinner: false, icon: '✓'  },
  failed:     { label: 'Failed',         badgeClass: 'badge-failed',     spinner: false, icon: '✕'  },
};

// HELPERS — HTML builders
function iconHTML(status) {
  const m = STATUS_META[status];
  return m.spinner
    ? `<div class="spinner"></div>`
    : `<span class="job-icon">${m.icon}</span>`;
}

function badgeHTML(status) {
  const m = STATUS_META[status];
  return `<span class="job-badge ${m.badgeClass}">${m.label}</span>`;
}

function inlineBadgeClass(status) {
  return `inline-status-badge ${STATUS_META[status].badgeClass}`;
}

// LIVE INDICATOR
function refreshLiveIndicator() {
  const anyActive = Object.values(jobs).some(
    j => j.status === 'uploading' || j.status === 'processing'
  );
  liveIndicator.classList.toggle('visible', anyActive);
}

// STATUS PANEL — create / update job row
function createStatusRow(job) {
  statusEmpty.style.display = 'none';

  const row = document.createElement('div');
  row.id        = `status-row-${job.id}`;
  row.className = `status-job status-${job.status}`;
  row.innerHTML = buildStatusRowHTML(job);
  statusJobList.prepend(row);
  job.statusPanelEl = row;
}

function updateStatusRow(job) {
  const row = job.statusPanelEl;
  if (!row) return;
  row.className = `status-job status-${job.status}`;
  row.innerHTML = buildStatusRowHTML(job);
}

function buildStatusRowHTML(job) {
  return `
    ${iconHTML(job.status)}
    <span class="job-name" title="${job.name}">${job.name}</span>
    <div class="job-progress-wrap">
      <div class="job-progress-bar" style="width:${job.progress}%"></div>
    </div>
    ${badgeHTML(job.status)}
  `;
}

//FILE LIST ROW — create / update inline badge
function createFileRow(job) {
  const existingEmpty = document.getElementById('emptyState');
  if (existingEmpty) existingEmpty.remove();

  const li = document.createElement('li');
  li.id        = `file-row-${job.id}`;
  li.innerHTML = `
    <span class="file-name">
      <span class="file-icon">📄</span>
      <span>${job.name}</span>
      <span class="${inlineBadgeClass(job.status)}" id="ibadge-${job.id}">
        ${STATUS_META[job.status].label}
      </span>
    </span>
    <div class="file-actions">
      <button data-job-id="${job.id}">Remove</button>
    </div>
  `;

  li.querySelector('button').addEventListener('click', () => removeJob(job.id));
  uploadedFiles.appendChild(li);
  job.fileListEl = li;
}

function updateFileRowBadge(job) {
  const badge = document.getElementById(`ibadge-${job.id}`);
  if (!badge) return;
  badge.className   = inlineBadgeClass(job.status);
  badge.textContent = STATUS_META[job.status].label;
}

// REMOVE JOB
function removeJob(id) {
  const job = jobs[id];
  if (!job) return;

  job.fileListEl?.remove();
  job.statusPanelEl?.remove();
  delete jobs[id];

  if (!Object.keys(jobs).length) {
    statusEmpty.style.display = '';
    const msg = document.createElement('li');
    msg.id        = 'emptyState';
    msg.className = 'empty-state';
    msg.textContent = 'No files uploaded yet.';
    uploadedFiles.appendChild(msg);
  }

  refreshLiveIndicator();
}

// OCR SIMULATED PIPELINE  (#221)
function simulateUpload(job) {
  return new Promise(resolve => {
    let pct = 0;
    const tick = setInterval(() => {
      pct = Math.min(pct + Math.random() * 18 + 5, 100);
      job.progress = Math.round(pct);
      updateStatusRow(job);

      progressBar.style.width   = job.progress + '%';
      progressBar.textContent   = job.progress + '%';

      if (pct >= 100) { clearInterval(tick); resolve(); }
    }, 220);
  });
}

function simulateOCR(job) {
  return new Promise((resolve, reject) => {
    const willFail = Math.random() < 0.10; // 10% failure rate for demo
    let pct = 0;
    const tick = setInterval(() => {
      pct = Math.min(pct + Math.random() * 12 + 4, 100);
      job.progress = Math.round(pct);
      updateStatusRow(job);
      updateFileRowBadge(job);

      if (pct >= 100) {
        clearInterval(tick);
        willFail ? reject(new Error('OCR engine error')) : resolve();
      }
    }, 300);
  });
}

async function runPipeline(job) {
  /* Stage 1 — Uploading */
  job.status   = 'uploading';
  job.progress = 0;
  createStatusRow(job);
  createFileRow(job);
  refreshLiveIndicator();

  progressCont.style.display = 'block';
  progressBar.style.width    = '0%';
  progressBar.textContent    = '0%';
  statusEl.textContent       = `Uploading ${job.name}…`;
  statusEl.className         = '';

  try {
    await simulateUpload(job);

    /* Stage 2 — OCR Processing */
    job.status   = 'processing';
    job.progress = 0;
    updateStatusRow(job);
    updateFileRowBadge(job);
    progressCont.style.display = 'none';
    statusEl.textContent       = `Processing ${job.name} through OCR…`;

    await simulateOCR(job);

    /* Stage 3 — Complete */
    job.status   = 'complete';
    job.progress = 100;
    updateStatusRow(job);
    updateFileRowBadge(job);
    statusEl.textContent = `✅ ${job.name} — OCR complete.`;

  } catch (err) {
    /* Stage — Failed */
    job.status   = 'failed';
    job.progress = 0;
    updateStatusRow(job);
    updateFileRowBadge(job);
    statusEl.textContent = `❌ ${job.name} — processing failed. Please retry.`;
    statusEl.className   = 'error';
  }

  refreshLiveIndicator();
}

// PDF VALIDATION  
function validatePDF(file) {
  if (!file)
    return { valid: false, message: '❌ No file selected.' };
  if (file.type !== 'application/pdf')
    return { valid: false, message: `❌ "${file.name}" was refused — only PDF files are accepted (received: ${file.type || 'unknown type'}).` };
  if (file.size === 0)
    return { valid: false, message: `❌ "${file.name}" was refused — file is empty.` };
  return { valid: true, message: '' };
}

function handleFileSelection(file) {
  const result = validatePDF(file);
  if (result.valid) {
    fileNameEl.textContent = file.name;
    uploadBtn.disabled     = false;
    statusEl.textContent   = '';
    statusEl.className     = '';
  } else {
    pdfInput.value         = '';
    fileNameEl.textContent = '';
    uploadBtn.disabled     = true;
    statusEl.textContent   = result.message;
    statusEl.className     = 'error';
  }
}

//   EVENT LISTENERS
// Drag & drop
['dragenter', 'dragover'].forEach(e =>
  dropArea.addEventListener(e, ev => { ev.preventDefault(); dropArea.classList.add('dragover'); })
);
['dragleave', 'drop'].forEach(e =>
  dropArea.addEventListener(e, ev => { ev.preventDefault(); dropArea.classList.remove('dragover'); })
);
dropArea.addEventListener('drop', ev => handleFileSelection(ev.dataTransfer.files[0]));

// File picker
pdfInput.addEventListener('change', () => handleFileSelection(pdfInput.files[0]));

// Upload — kick off pipeline
uploadBtn.addEventListener('click', () => {
  const file = pdfInput.files[0];
  if (!file) return;

  const job = {
    id:            `job-${Date.now()}`,
    name:          file.name,
    status:        'uploading',
    progress:      0,
    fileListEl:    null,
    statusPanelEl: null,
  };
  jobs[job.id] = job;

  pdfInput.value         = '';
  fileNameEl.textContent = '';
  uploadBtn.disabled     = true;

  runPipeline(job);
});
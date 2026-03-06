/* ══════════════════════════════════════════════════════════════
   upload.js  —  File Manager logic
   Flow:
     1. User drops / selects one or more PDFs
     2. Each file uploads immediately (real POST /upload)
     3. On upload complete → appears in "Ready for OCR" queue
     4. User clicks "Run OCR" (per file) or "Run OCR on All"
     5. OCR runs (simulated — swap simulateOCR() for real call)
     6. On OCR complete → file moves to "Completed PDFs" section
══════════════════════════════════════════════════════════════ */

/* ── Element refs ─────────────────────────────────────────────── */
const dropArea      = document.getElementById('dropArea');
const pdfInput      = document.getElementById('pdfInput');
const uploadStatus  = document.getElementById('uploadStatus');
const queueList     = document.getElementById('queueList');
const queueEmpty    = document.getElementById('queueEmpty');
const completedList = document.getElementById('completedList');
const completedEmpty= document.getElementById('completedEmpty');
const runAllBtn     = document.getElementById('runAllBtn');
const liveIndicator = document.getElementById('liveIndicator');

/* ── Job registry ─────────────────────────────────────────────── */
// jobId → { id, name, file, state, rowEl }
// states: 'uploading' | 'ready' | 'processing' | 'failed'
const jobs = {};

/* ══════════════════════════════════════════════════════════════
   QUEUE EMPTY STATE + RUN-ALL BUTTON
══════════════════════════════════════════════════════════════ */
function refreshQueueUI() {
  const allJobs   = Object.values(jobs);
  const readyJobs = allJobs.filter(j => j.state === 'ready');
  const anyActive = allJobs.some(
    j => j.state === 'uploading' || j.state === 'processing'
  );

  // Show/hide empty placeholder
  if (queueEmpty) queueEmpty.style.display = allJobs.length ? 'none' : '';

  // Run All enabled only when at least one ready job exists
  runAllBtn.disabled = readyJobs.length === 0;

  // Live indicator
  liveIndicator.classList.toggle('visible', anyActive);
}

function refreshCompletedUI() {
  const hasCompleted = completedList.querySelectorAll('li:not(#completedEmpty)').length > 0;
  if (completedEmpty) completedEmpty.style.display = hasCompleted ? 'none' : '';
}

/* ══════════════════════════════════════════════════════════════
   QUEUE ROW — build & update
══════════════════════════════════════════════════════════════ */
function createQueueRow(job) {
  if (queueEmpty) queueEmpty.style.display = 'none';

  const li = document.createElement('li');
  li.id        = `qrow-${job.id}`;
  li.className = `queue-item state-${job.state}`;
  li.innerHTML = `
    <span class="file-icon">📄</span>
    <span class="item-name" title="${job.name}">${job.name}</span>
    <div class="item-progress-wrap" id="prog-wrap-${job.id}">
      <div class="item-progress-bar" id="prog-bar-${job.id}"></div>
    </div>
    <div class="spinner" id="spinner-${job.id}"></div>
    <span class="item-badge badge-${job.state}" id="badge-${job.id}">
      ${stateName(job.state)}
    </span>
    <div class="item-actions" id="actions-${job.id}">
      <button class="btn-ocr"    id="btn-ocr-${job.id}"    disabled>Run OCR</button>
      <button class="btn-remove" id="btn-remove-${job.id}">✕</button>
    </div>
  `;

  document.getElementById(`btn-ocr-${job.id}`)
    ?.addEventListener('click', () => startOCR(job.id));
  document.getElementById(`btn-remove-${job.id}`)
    ?.addEventListener('click', () => removeQueueJob(job.id));

  queueList.appendChild(li);
  job.rowEl = li;
}

function updateQueueRow(job) {
  const li = job.rowEl;
  if (!li) return;

  li.className = `queue-item state-${job.state}`;

  // Badge
  const badge = document.getElementById(`badge-${job.id}`);
  if (badge) {
    badge.className   = `item-badge badge-${job.state}`;
    badge.textContent = stateName(job.state);
  }

  // Progress bar visibility
  const progWrap = document.getElementById(`prog-wrap-${job.id}`);
  const progBar  = document.getElementById(`prog-bar-${job.id}`);
  const spinner  = document.getElementById(`spinner-${job.id}`);
  const isActive = job.state === 'uploading' || job.state === 'processing';

  if (progWrap) progWrap.style.display = isActive ? 'block' : 'none';
  if (progBar)  progBar.style.width    = job.progress + '%';
  if (spinner)  spinner.style.display  = isActive ? 'block' : 'none';

  // OCR button — enabled only when ready
  const ocrBtn    = document.getElementById(`btn-ocr-${job.id}`);
  const removeBtn = document.getElementById(`btn-remove-${job.id}`);
  if (ocrBtn)    ocrBtn.disabled    = job.state !== 'ready';
  if (removeBtn) removeBtn.disabled = isActive;
}

function stateName(state) {
  return { uploading: 'Uploading', ready: 'Ready', processing: 'Processing', failed: 'Failed' }[state] ?? state;
}

/* ══════════════════════════════════════════════════════════════
   REMOVE FROM QUEUE
══════════════════════════════════════════════════════════════ */
function removeQueueJob(id) {
  const job = jobs[id];
  if (!job) return;
  job.rowEl?.remove();
  delete jobs[id];
  refreshQueueUI();
}

/* ══════════════════════════════════════════════════════════════
   COMPLETED ROW
══════════════════════════════════════════════════════════════ */
function moveToCompleted(job) {
  // Remove from queue
  job.rowEl?.remove();
  delete jobs[job.id];
  refreshQueueUI();

  // Add to completed list
  if (completedEmpty) completedEmpty.style.display = 'none';

  const li = document.createElement('li');
  li.innerHTML = `
    <span class="completed-name">
      <span class="file-icon">📄</span>
      <span title="${job.name}">${job.name}</span>
      <span class="item-badge badge-complete">Complete</span>
    </span>
    <button class="btn-completed-remove">✕</button>
  `;
  li.querySelector('.btn-completed-remove')
    .addEventListener('click', () => { li.remove(); refreshCompletedUI(); });

  completedList.appendChild(li);
  refreshCompletedUI();
}

/* ══════════════════════════════════════════════════════════════
   STAGE 1 — REAL UPLOAD  (POST /upload)
   Progress tracked via XHR upload events.
══════════════════════════════════════════════════════════════ */
function doUpload(job) {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('pdfFile', job.file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload');

    xhr.upload.onprogress = e => {
      if (e.lengthComputable) {
        job.progress = Math.round((e.loaded / e.total) * 100);
        updateQueueRow(job);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        resolve();
      } else {
        let msg = `Server responded with ${xhr.status}`;
        try { const b = JSON.parse(xhr.responseText); if (b.error) msg = b.error; } catch (_) {}
        reject(new Error(msg));
      }
    };

    xhr.onerror = () => reject(new Error('Network error — is the server running?'));
    xhr.send(formData);
  });
}

async function uploadFile(job) {
  job.state    = 'uploading';
  job.progress = 0;
  createQueueRow(job);
  refreshQueueUI();

  try {
    await doUpload(job);
    job.state    = 'ready';
    job.progress = 0;
    updateQueueRow(job);
  } catch (err) {
    job.state = 'failed';
    updateQueueRow(job);
    uploadStatus.textContent = `❌ ${job.name}: ${err.message}`;
    uploadStatus.className   = 'error';
    console.error('[upload.js] Upload failed:', err);
  }

  refreshQueueUI();
}

/* ══════════════════════════════════════════════════════════════
   STAGE 2 — SIMULATED OCR
   Replace simulateOCR() with a real fetch('/ocr/:id') when ready.
══════════════════════════════════════════════════════════════ */
function simulateOCR(job) {
  return new Promise((resolve, reject) => {
    let pct = 0;
    const tick = setInterval(() => {
      pct = Math.min(pct + Math.random() * 12 + 4, 100);
      job.progress = Math.round(pct);
      updateQueueRow(job);
      if (pct >= 100) {
        clearInterval(tick);
        resolve();
      }
    }, 280);
  });
}

async function startOCR(id) {
  const job = jobs[id];
  if (!job || job.state !== 'ready') return;

  job.state    = 'processing';
  job.progress = 0;
  updateQueueRow(job);
  refreshQueueUI();

  try {
    await simulateOCR(job);
    moveToCompleted(job);
  } catch (err) {
    job.state = 'failed';
    updateQueueRow(job);
    refreshQueueUI();
    console.error('[upload.js] OCR failed:', err);
  }
}

/* ── Run OCR on All ready files ───────────────────────────────── */
function startOCRAll() {
  Object.values(jobs)
    .filter(j => j.state === 'ready')
    .forEach(j => startOCR(j.id));
}

/* ══════════════════════════════════════════════════════════════
   PDF VALIDATION
══════════════════════════════════════════════════════════════ */
function validatePDF(file) {
  if (!file)
    return { valid: false, message: `❌ No file selected.` };
  if (file.type !== 'application/pdf')
    return { valid: false, message: `❌ "${file.name}" refused — only PDFs accepted (got: ${file.type || 'unknown'}).` };
  if (file.size === 0)
    return { valid: false, message: `❌ "${file.name}" refused — file is empty.` };
  return { valid: true };
}

/* ══════════════════════════════════════════════════════════════
   HANDLE FILE SELECTION (multi-file)
══════════════════════════════════════════════════════════════ */
function handleFiles(fileList) {
  const files  = Array.from(fileList);
  const errors = [];

  uploadStatus.textContent = '';
  uploadStatus.className   = '';

  files.forEach(file => {
    const result = validatePDF(file);
    if (!result.valid) {
      errors.push(result.message);
      return;
    }

    const job = {
      id:       `job-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      name:     file.name,
      file,
      state:    'uploading',
      progress: 0,
      rowEl:    null,
    };
    jobs[job.id] = job;
    uploadFile(job);
  });

  if (errors.length) {
    uploadStatus.textContent = errors.join(' • ');
    uploadStatus.className   = 'error';
  }

  // Reset input so same files can be re-selected if needed
  pdfInput.value = '';
}

/* ══════════════════════════════════════════════════════════════
   EVENT LISTENERS
══════════════════════════════════════════════════════════════ */

// Drag & drop
['dragenter', 'dragover'].forEach(e =>
  dropArea.addEventListener(e, ev => { ev.preventDefault(); dropArea.classList.add('dragover'); })
);
['dragleave', 'drop'].forEach(e =>
  dropArea.addEventListener(e, ev => { ev.preventDefault(); dropArea.classList.remove('dragover'); })
);
dropArea.addEventListener('drop', ev => handleFiles(ev.dataTransfer.files));

// File picker (multiple)
pdfInput.addEventListener('change', () => handleFiles(pdfInput.files));

// Run OCR on All
runAllBtn.addEventListener('click', startOCRAll);
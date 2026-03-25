/* ══════════════════════════════════════════════════════════════
   upload.js  —  File Manager logic
   Flow:
     1. User drops / selects one or more PDFs
     2. Each file uploads immediately (real POST /upload)
        → server returns jobId, pipeline starts in background
     3. On upload complete → appears in "Ready for OCR" queue
     4. User clicks "Run OCR" (per file) or "Run OCR on All"
     5. Frontend polls GET /job/:id for live stage + progress
        Stages: ocr → extracting → done | failed
     6. On done → SSE push from GET /processed-files/stream
        updates "Completed PDFs" section in real time.

    Persistent Completed List
     • On page load: GET /processed-files populates completed list
       from the OCR-processed directory on the server.
     • Real-time: SSE (GET /processed-files/stream) pushes new
       entries as they finish, no polling needed.
     • Actions per completed item:
         - View     → modal with OCR text (existing openTxtModal)
         - Download → fetches /ocr-result/:filename as blob
         - Re-run OCR → re-queues file via POST /rerun/:filename
         - Delete   → DELETE /processed-files/:filename + remove row
══════════════════════════════════════════════════════════════ */

/* ── Element refs ─────────────────────────────────────────────── */
const dropArea      = document.getElementById('dropArea');
const pdfInput      = document.getElementById('pdfInput');
const uploadStatus  = document.getElementById('uploadStatus');
const queueList     = document.getElementById('queueList');
const queueEmpty    = document.getElementById('queueEmpty');
const completedList    = document.getElementById('completedList');
const completedEmpty   = document.getElementById('completedEmpty');
const completedLoading = document.getElementById('completedLoading'); // #259
const sseIndicator     = document.getElementById('sseIndicator');     // #259
const runAllBtn        = document.getElementById('runAllBtn');
const liveIndicator    = document.getElementById('liveIndicator');

/* ── Job registry ─────────────────────────────────────────────── */
// jobId → { id, name, file, state, rowEl }
// states: 'uploading' | 'ready' | 'processing' | 'failed'
const jobs = {};

/* ── Completed file registry ──────────────────────────────────── */
// #259: Track txt filenames already rendered so SSE doesn't
// add duplicates for files that were loaded on page load.
const completedFilenames = new Set();

/* ══════════════════════════════════════════════════════════════
   QUEUE EMPTY STATE + RUN-ALL BUTTON
══════════════════════════════════════════════════════════════ */
function refreshQueueUI() {
  const allJobs   = Object.values(jobs);
  const readyJobs = allJobs.filter(j => j.state === 'ready');
  const anyActive = allJobs.some(
    j => j.state === 'uploading' || j.state === 'processing'
  );
  if (queueEmpty)  queueEmpty.style.display  = allJobs.length ? 'none' : '';
  runAllBtn.disabled = readyJobs.length === 0;
  liveIndicator.classList.toggle('visible', anyActive);
}

function refreshCompletedUI() {
  // Only show the empty state once the initial load has finished
  // (completedLoading hidden = load complete). While loading is visible
  // we don't want to flash "No completed files yet".
  const isLoading = completedLoading && completedLoading.style.display !== 'none';
  if (isLoading) return;
  const hasCompleted = completedFilenames.size > 0;
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
    <div class="item-progress-wrap" id="prog-wrap-${job.id}" style="display:none">
      <div class="item-progress-bar" id="prog-bar-${job.id}"></div>
    </div>
    <div class="spinner" id="spinner-${job.id}" style="display:none"></div>
    <span class="item-badge badge-${job.state}" id="badge-${job.id}">${stateName(job.state)}</span>
    <div class="item-actions">
      <button class="btn-ocr"   id="btn-ocr-${job.id}"   disabled>Run OCR</button>
      <button class="btn-retry" id="btn-retry-${job.id}" style="display:none">↺ Retry</button>
      <button class="btn-remove" id="btn-remove-${job.id}">✕</button>
    </div>
    <div class="item-error" id="error-${job.id}" style="display:none"></div>
  `;

  // Attach listeners directly to the elements — never wiped since we
  // only update child elements (badge, progress, spinner) not innerHTML
  li.querySelector(`#btn-ocr-${job.id}`)
    .addEventListener('click', () => startOCR(job.id));
  li.querySelector(`#btn-retry-${job.id}`)
    .addEventListener('click', () => startOCR(job.id));
  li.querySelector(`#btn-remove-${job.id}`)
    .addEventListener('click', () => removeQueueJob(job.id));

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
    const label = (job.state === 'processing' && job.stageLabel)
      ? job.stageLabel : stateName(job.state);
    badge.className   = `item-badge badge-${job.state}`;
    badge.textContent = label;
  }

  // Progress bar + spinner — only visible while active
  const isActive = job.state === 'uploading' || job.state === 'processing';
  const progWrap = document.getElementById(`prog-wrap-${job.id}`);
  const progBar  = document.getElementById(`prog-bar-${job.id}`);
  const spinner  = document.getElementById(`spinner-${job.id}`);
  if (progWrap) progWrap.style.display = isActive ? 'block' : 'none';
  if (progBar)  progBar.style.width    = job.progress + '%';
  if (spinner)  spinner.style.display  = isActive ? 'block' : 'none';

  // OCR button, retry button, remove button states
  const ocrBtn    = document.getElementById(`btn-ocr-${job.id}`);
  const retryBtn  = document.getElementById(`btn-retry-${job.id}`);
  const removeBtn = document.getElementById(`btn-remove-${job.id}`);
  const errorDiv  = document.getElementById(`error-${job.id}`);

  if (ocrBtn)    ocrBtn.disabled             = job.state !== 'ready';
  if (ocrBtn)    ocrBtn.style.display        = job.state === 'failed' ? 'none' : '';
  if (retryBtn)  retryBtn.style.display      = (job.state === 'failed' && job.canRetry) ? '' : 'none';
  if (removeBtn) removeBtn.disabled          = job.state === 'uploading';

  // Error message — shown only on failure
  if (errorDiv) {
    if (job.state === 'failed' && job.errorMsg) {
      errorDiv.textContent = `⚠️ ${job.errorMsg}`;
      errorDiv.style.display = 'block';
    } else {
      errorDiv.style.display = 'none';
    }
  }
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
   COMPLETED ROW (persistent, server-linked)

   addCompletedRow({ pdfName, txtFilename, processedAt })
     Builds a completed list row with View / Download /
     Re-run OCR / Delete actions.  Safe to call from both
     the initial page-load fetch and the SSE handler —
     completedFilenames guards against duplicates.
══════════════════════════════════════════════════════════════ */
function addCompletedRow({ pdfName, txtFilename, processedAt }) {
  // Guard: skip if already rendered (e.g. SSE fires for a file
  // that was already loaded on page load)
  if (completedFilenames.has(txtFilename)) return;
  completedFilenames.add(txtFilename);

  if (completedEmpty) completedEmpty.style.display = 'none';

  const dateLabel = processedAt
    ? new Date(processedAt).toLocaleString()
    : '';

  const li = document.createElement('li');
  li.dataset.txtFilename = txtFilename;
  li.innerHTML = `
    <span class="completed-name">
      <span class="file-icon">📄</span>
      <span title="${pdfName}">${pdfName}</span>
      <span class="item-badge badge-complete">Complete</span>
      ${dateLabel ? `<span class="completed-date">${dateLabel}</span>` : ''}
    </span>
    <div class="completed-actions">
      <button class="btn-view-txt"    title="View OCR text">View</button>
      <button class="btn-download-txt" title="Download .txt file">⬇ Download</button>
      <button class="btn-rerun-ocr"   title="Re-queue for OCR">↺ Re-run OCR</button>
      <button class="btn-delete-file" title="Delete from server">🗑 Delete</button>
    </div>
  `;

  // View
  li.querySelector('.btn-view-txt')
    .addEventListener('click', () => openTxtModal(pdfName, txtFilename));

  // Download
  li.querySelector('.btn-download-txt')
    .addEventListener('click', () => downloadTxt(txtFilename));

  // Re-run OCR — asks server to re-queue the original PDF
  li.querySelector('.btn-rerun-ocr')
    .addEventListener('click', () => rerunOCR(pdfName, txtFilename, li));

  // Delete from server
  li.querySelector('.btn-delete-file')
    .addEventListener('click', () => deleteCompleted(txtFilename, li));

  completedList.appendChild(li);
}

/* ── #259 helper: remove a completed row cleanly ─────────────── */
function removeCompletedRow(txtFilename, liEl) {
  completedFilenames.delete(txtFilename);
  liEl.remove();
  refreshCompletedUI();
}

/* ══════════════════════════════════════════════════════════════
   #259 — COMPLETED ROW ACTIONS
══════════════════════════════════════════════════════════════ */

/* Download the .txt file as a browser file download */
async function downloadTxt(txtFilename) {
  try {
    const res = await fetch(`/ocr-result/${encodeURIComponent(txtFilename)}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = txtFilename;
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    console.error('[upload.js] Download failed:', err.message);
    alert(`Download failed: ${err.message}`);
  }
}

/* Re-queue the file for OCR — server must still have the original PDF.
   POST /rerun/:txtFilename  →  { jobId, pdfName }
   The completed row is removed immediately; the job re-enters the
   queue section so the user can see its progress as normal. */
async function rerunOCR(pdfName, txtFilename, liEl) {
  if (!confirm(`Re-run OCR on "${pdfName}"? The current result will be replaced when complete.`)) return;

  try {
    const res = await fetch(`/rerun/${encodeURIComponent(txtFilename)}`, { method: 'POST' });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }
    const { jobId } = await res.json();

    // Remove from completed list so SSE re-adds it fresh when done
    removeCompletedRow(txtFilename, liEl);

    // Register a skeleton job so the queue row appears immediately
    const job = {
      id:       jobId,
      name:     pdfName,
      file:     null,           // original file not in memory
      serverId: jobId,
      state:    'processing',
      stageLabel: 'OCR',
      progress: 0,
      rowEl:    null,
    };
    jobs[jobId] = job;
    createQueueRow(job);
    refreshQueueUI();

    // Resume polling — on done the SSE will re-add it to completed
    await pollJobUntilDone(job);
    // pollJobUntilDone resolves on 'done'; SSE handles the completed row
    job.rowEl?.remove();
    delete jobs[jobId];
    refreshQueueUI();
  } catch (err) {
    console.error('[upload.js] Re-run OCR failed:', err.message);
    alert(`Re-run failed: ${err.message}`);
  }
}

/* Delete the processed file from the server */
async function deleteCompleted(txtFilename, liEl) {
  if (!confirm(`Delete "${txtFilename}" from the server? This cannot be undone.`)) return;

  try {
    const res = await fetch(`/processed-files/${encodeURIComponent(txtFilename)}`, {
      method: 'DELETE',
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }
    removeCompletedRow(txtFilename, liEl);
  } catch (err) {
    console.error('[upload.js] Delete failed:', err.message);
    alert(`Delete failed: ${err.message}`);
  }
}

/* ══════════════════════════════════════════════════════════════
   #259 — PAGE-LOAD FETCH  (GET /processed-files)
   Populates "Completed PDFs" from the server's OCR output
   directory so the list survives page refreshes.

   Expected response shape:
   [
     { pdfName: "foo.pdf", txtFilename: "foo.txt", processedAt: "<ISO>" },
     ...
   ]
══════════════════════════════════════════════════════════════ */
async function loadProcessedFiles() {
  // #259: Show spinner while fetching; always hide it when done
  if (completedLoading) completedLoading.style.display = 'flex';

  try {
    const res = await fetch('/processed-files');
    if (!res.ok) throw new Error(`Server responded with ${res.status}`);
    const files = await res.json();

    if (!Array.isArray(files)) throw new Error('Unexpected response format');

    files.forEach(entry => addCompletedRow(entry));
  } catch (err) {
    console.error('[upload.js] Could not load processed files:', err.message);
    // Non-fatal — the list stays empty; SSE may still deliver new files
  } finally {
    if (completedLoading) completedLoading.style.display = 'none';
    refreshCompletedUI(); // show empty state now if nothing came back
  }
}

/* ══════════════════════════════════════════════════════════════
   #259 — SSE LISTENER  (GET /processed-files/stream)
   Server pushes an event whenever a new file lands in the
   OCR-processed directory.  Keeps the completed list live
   without the frontend needing to poll.

   Expected SSE event data (JSON string):
   { pdfName: "bar.pdf", txtFilename: "bar.txt", processedAt: "<ISO>" }
══════════════════════════════════════════════════════════════ */
function connectProcessedFilesSSE() {
  const sse = new EventSource('/processed-files/stream');

  // #259: Light up the SSE indicator when the connection opens
  sse.addEventListener('open', () => {
    if (sseIndicator) sseIndicator.classList.add('connected');
  });

  sse.addEventListener('processed-file', e => {
    try {
      const entry = JSON.parse(e.data);
      addCompletedRow(entry);
      refreshCompletedUI();
    } catch (err) {
      console.error('[upload.js] SSE parse error:', err.message);
    }
  });

  sse.addEventListener('error', () => {
    // Dim the indicator while disconnected; it re-lights on next 'open'
    if (sseIndicator) sseIndicator.classList.remove('connected');
    console.warn('[upload.js] SSE connection lost — will auto-reconnect.');
    // EventSource reconnects automatically; no manual retry needed
  });
}

/* ══════════════════════════════════════════════════════════════
   STAGE 1 — REAL UPLOAD  (POST /upload)
   Progress tracked via XHR upload events.
   Server returns jobId which is stored on the job for polling.
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
        try {
          const body  = JSON.parse(xhr.responseText);
          job.serverId = body.jobId; // store server-side job ID for polling
          resolve();
        } catch (_) {
          reject(new Error('Invalid server response'));
        }
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
   STAGE 2 — MANUAL OCR TRIGGER + POLLING  (#223)
   Button calls POST /ocr/:serverId to start, then polls
   GET /job/:serverId every 1.5s for progress until done.
   On failure: shows server error message + retry button if allowed.
   On success: SSE delivers the completed-file event which calls
   addCompletedRow(); moveToCompleted() is no longer used.
══════════════════════════════════════════════════════════════ */
const STAGE_LABELS = {
  ocr:    'OCR',
  done:   'Done',
  failed: 'Failed',
};

function pollJobUntilDone(job) {
  return new Promise((resolve, reject) => {
    const interval = setInterval(async () => {
      try {
        const res  = await fetch(`/job/${job.serverId}`);
        if (!res.ok) throw new Error(`Poll failed: ${res.status}`);
        const data = await res.json();

        job.progress   = data.progress ?? job.progress;
        job.stageLabel = STAGE_LABELS[data.stage] ?? data.stage;
        job.canRetry   = data.canRetry ?? false;
        updateQueueRow(job);

        if (data.stage === 'done') {
          clearInterval(interval);
          if (data.result?.warnings) {
            console.warn(`[upload.js] OCR done with warnings: ${data.result.warnings}`);
          }
          resolve();
        } else if (data.stage === 'failed') {
          clearInterval(interval);
          reject(new Error(data.error || 'OCR failed on server'));
        }
      } catch (err) {
        clearInterval(interval);
        reject(err);
      }
    }, 1500);
  });
}

async function startOCR(id) {
  const job = jobs[id];
  if (!job || (job.state !== 'ready' && job.state !== 'failed')) return;

  if (!job.serverId) {
    job.state      = 'failed';
    job.errorMsg   = 'Upload did not complete — please remove and re-upload this file.';
    updateQueueRow(job);
    refreshQueueUI();
    return;
  }

  job.state      = 'processing';
  job.stageLabel = 'OCR';
  job.progress   = 0;
  job.errorMsg   = null;
  updateQueueRow(job);
  refreshQueueUI();

  try {
    const triggerRes = await fetch(`/ocr/${job.serverId}`, { method: 'POST' });
    if (!triggerRes.ok) {
      const body = await triggerRes.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${triggerRes.status}`);
    }

    await pollJobUntilDone(job);

    // #259: Completed row is now driven by SSE (addCompletedRow).
    // Just clean up the queue row here.
    job.rowEl?.remove();
    delete jobs[job.id];
    refreshQueueUI();
  } catch (err) {
    job.state    = 'failed';
    job.errorMsg = err.message;
    updateQueueRow(job);
    refreshQueueUI();
    console.error('[upload.js] OCR failed:', err.message);
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

/* ══════════════════════════════════════════════════════════════
   TXT RESULT MODAL  (#222)
   Opens a modal showing the raw OCR text for a completed file.
   Fetches GET /ocr-result/:filename from the server.
══════════════════════════════════════════════════════════════ */
async function openTxtModal(pdfName, txtFilename) {
  const modal    = document.getElementById('txtModal');
  const title    = document.getElementById('txtModalTitle');
  const content  = document.getElementById('txtModalContent');
  const loading  = document.getElementById('txtModalLoading');

  // Show modal in loading state
  title.textContent    = pdfName;
  content.style.display  = 'none';
  loading.style.display  = 'block';
  modal.style.display    = 'flex';

  try {
    const res = await fetch(`/ocr-result/${encodeURIComponent(txtFilename)}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }
    const text = await res.text();
    content.textContent   = text;
    content.style.display = 'block';
    loading.style.display = 'none';
  } catch (err) {
    content.textContent   = `❌ Could not load OCR text: ${err.message}`;
    content.style.display = 'block';
    loading.style.display = 'none';
  }
}

function closeTxtModal() {
  document.getElementById('txtModal').style.display = 'none';
}

// Close modal on backdrop click
document.getElementById('txtModal')
  .addEventListener('click', e => { if (e.target.id === 'txtModal') closeTxtModal(); });

// Close on Escape key
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeTxtModal(); });

/* ══════════════════════════════════════════════════════════════
   INIT
   Load persisted files first, then open SSE for live updates.
══════════════════════════════════════════════════════════════ */
(async () => {
  await loadProcessedFiles();   // populate from OCR-processed directory
  connectProcessedFilesSSE();   // keep list live as new files arrive
})();
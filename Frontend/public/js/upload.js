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
     • Real-time: SSE pushes new entries as they finish
     • Actions per completed item:
         - View     → modal with OCR text
         - Edit     → #248 in-modal textarea editor
         - Download → fetches /ocr-result/:filename as blob
         - Re-run OCR → re-queues file via POST /rerun/:filename
         - Delete   → DELETE /processed-files/:filename + remove row

    #248 Edit Modal Features
     • Edit toggle   — switches <pre> ↔ <textarea>
     • Save          — PUT /processed-files/:filename with new text
     • Cancel        — reverts textarea; warns if unsaved changes
     • Diff view     — side-by-side original (server) vs current edits
     • Find & Replace— operates on the live textarea content
     • Unsaved guard — fires on close / cancel / backdrop click
══════════════════════════════════════════════════════════════ */

/* ── Element refs ─────────────────────────────────────────────── */
const dropArea      = document.getElementById('dropArea');
const pdfInput      = document.getElementById('pdfInput');
const uploadStatus  = document.getElementById('uploadStatus');
const queueList     = document.getElementById('queueList');
const queueEmpty    = document.getElementById('queueEmpty');
const completedList    = document.getElementById('completedList');
const completedEmpty   = document.getElementById('completedEmpty');
const completedLoading = document.getElementById('completedLoading');
const sseIndicator     = document.getElementById('sseIndicator');
const runAllBtn        = document.getElementById('runAllBtn');
const liveIndicator    = document.getElementById('liveIndicator');

/* ── Job registry ─────────────────────────────────────────────── */
const jobs = {};

/* ── Completed file registry ──────────────────────────────────── */
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

  const badge = document.getElementById(`badge-${job.id}`);
  if (badge) {
    const label = (job.state === 'processing' && job.stageLabel)
      ? job.stageLabel : stateName(job.state);
    badge.className   = `item-badge badge-${job.state}`;
    badge.textContent = label;
  }

  const isActive = job.state === 'uploading' || job.state === 'processing';
  const progWrap = document.getElementById(`prog-wrap-${job.id}`);
  const progBar  = document.getElementById(`prog-bar-${job.id}`);
  const spinner  = document.getElementById(`spinner-${job.id}`);
  if (progWrap) progWrap.style.display = isActive ? 'block' : 'none';
  if (progBar)  progBar.style.width    = job.progress + '%';
  if (spinner)  spinner.style.display  = isActive ? 'block' : 'none';

  const ocrBtn    = document.getElementById(`btn-ocr-${job.id}`);
  const retryBtn  = document.getElementById(`btn-retry-${job.id}`);
  const removeBtn = document.getElementById(`btn-remove-${job.id}`);
  const errorDiv  = document.getElementById(`error-${job.id}`);

  if (ocrBtn)    ocrBtn.disabled             = job.state !== 'ready';
  if (ocrBtn)    ocrBtn.style.display        = job.state === 'failed' ? 'none' : '';
  if (retryBtn)  retryBtn.style.display      = (job.state === 'failed' && job.canRetry) ? '' : 'none';
  if (removeBtn) removeBtn.disabled          = job.state === 'uploading';

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
   COMPLETED ROW
══════════════════════════════════════════════════════════════ */
function addCompletedRow({ pdfName, txtFilename, processedAt }) {
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
      <!-- View: eye -->
      <button class="btn-view-txt" title="View OCR text">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
      </button>
      <!-- Download: arrow down to line -->
      <button class="btn-download-txt" title="Download .txt file">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v13"/><path d="M8 12l4 4 4-4"/><path d="M3 20h18"/></svg>
      </button>
      <!-- Re-run OCR: refresh -->
      <button class="btn-rerun-ocr" title="Re-run OCR">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.5"/></svg>
      </button>
      <!-- Delete: trash -->
      <button class="btn-delete-file" title="Delete from server">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/></svg>
      </button>
    </div>
  `;

  li.querySelector('.btn-view-txt')
    .addEventListener('click', () => openTxtModal(pdfName, txtFilename));

  li.querySelector('.btn-download-txt')
    .addEventListener('click', () => downloadTxt(txtFilename));

  li.querySelector('.btn-rerun-ocr')
    .addEventListener('click', () => rerunOCR(pdfName, txtFilename, li));

  li.querySelector('.btn-delete-file')
    .addEventListener('click', () => deleteCompleted(txtFilename, li));

  completedList.appendChild(li);
}

function removeCompletedRow(txtFilename, liEl) {
  completedFilenames.delete(txtFilename);
  liEl.remove();
  refreshCompletedUI();
}

/* ══════════════════════════════════════════════════════════════
   COMPLETED ROW ACTIONS
══════════════════════════════════════════════════════════════ */
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

async function rerunOCR(pdfName, txtFilename, liEl) {
  if (!confirm(`Re-run OCR on "${pdfName}"? The current result will be replaced when complete.`)) return;

  try {
    const res = await fetch(`/rerun/${encodeURIComponent(txtFilename)}`, { method: 'POST' });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }
    const { jobId } = await res.json();

    removeCompletedRow(txtFilename, liEl);

    const job = {
      id:         jobId,
      name:       pdfName,
      file:       null,
      serverId:   jobId,
      state:      'processing',
      stageLabel: 'OCR',
      progress:   0,
      rowEl:      null,
    };
    jobs[jobId] = job;
    createQueueRow(job);
    refreshQueueUI();

    await pollJobUntilDone(job);
    job.rowEl?.remove();
    delete jobs[jobId];
    refreshQueueUI();
  } catch (err) {
    console.error('[upload.js] Re-run OCR failed:', err.message);
    alert(`Re-run failed: ${err.message}`);
  }
}

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
   PAGE-LOAD FETCH  (GET /processed-files)
══════════════════════════════════════════════════════════════ */
async function loadProcessedFiles() {
  if (completedLoading) completedLoading.style.display = 'flex';

  try {
    const res = await fetch('/processed-files');
    if (!res.ok) throw new Error(`Server responded with ${res.status}`);
    const files = await res.json();

    if (!Array.isArray(files)) throw new Error('Unexpected response format');

    files.forEach(entry => addCompletedRow(entry));
  } catch (err) {
    console.error('[upload.js] Could not load processed files:', err.message);
  } finally {
    if (completedLoading) completedLoading.style.display = 'none';
    refreshCompletedUI();
  }
}

/* ══════════════════════════════════════════════════════════════
   SSE LISTENER  (GET /processed-files/stream)
══════════════════════════════════════════════════════════════ */
function connectProcessedFilesSSE() {
  const sse = new EventSource('/processed-files/stream');

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
    if (sseIndicator) sseIndicator.classList.remove('connected');
    console.warn('[upload.js] SSE connection lost — will auto-reconnect.');
  });
}

/* ══════════════════════════════════════════════════════════════
   STAGE 1 — REAL UPLOAD  (POST /upload)
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
          const body   = JSON.parse(xhr.responseText);
          job.serverId = body.jobId;
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
   STAGE 2 — OCR TRIGGER + POLLING
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
    job.state    = 'failed';
    job.errorMsg = 'Upload did not complete — please remove and re-upload this file.';
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
   HANDLE FILE SELECTION
══════════════════════════════════════════════════════════════ */
function handleFiles(fileList) {
  const files  = Array.from(fileList);
  const errors = [];

  uploadStatus.textContent = '';
  uploadStatus.className   = '';

  files.forEach(file => {
    const result = validatePDF(file);
    if (!result.valid) { errors.push(result.message); return; }

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

  pdfInput.value = '';
}

/* ══════════════════════════════════════════════════════════════
   EVENT LISTENERS (drop, file picker, run-all)
══════════════════════════════════════════════════════════════ */
['dragenter', 'dragover'].forEach(e =>
  dropArea.addEventListener(e, ev => { ev.preventDefault(); dropArea.classList.add('dragover'); })
);
['dragleave', 'drop'].forEach(e =>
  dropArea.addEventListener(e, ev => { ev.preventDefault(); dropArea.classList.remove('dragover'); })
);
dropArea.addEventListener('drop', ev => handleFiles(ev.dataTransfer.files));
pdfInput.addEventListener('change', () => handleFiles(pdfInput.files));
runAllBtn.addEventListener('click', startOCRAll);


/* ══════════════════════════════════════════════════════════════
   #248 — TXT VIEW / EDIT MODAL
   ─────────────────────────────────────────────────────────────
   Modal state machine
     mode: 'view' | 'edit' | 'diff'
     modalState.originalText  — text as loaded from server
     modalState.currentFile   — { pdfName, txtFilename }
     modalState.isDirty       — textarea differs from originalText

   Toolbar interactions:
     tbEdit   → toggle view ↔ edit
     tbDiff   → toggle diff panel (only while in edit mode)
     tbFind   → toggle find & replace bar
     tbSave   → PUT /processed-files/:txtFilename
     tbCancel → revert + exit edit mode (warns if dirty)

   Unsaved guard fires on:
     • Close button click
     • Backdrop click
     • Escape key
     • tbCancel click (when dirty)
══════════════════════════════════════════════════════════════ */

/* ── Modal element refs ───────────────────────────────────────── */
const txtModal        = document.getElementById('txtModal');
const txtModalTitle   = document.getElementById('txtModalTitle');
const txtUnsavedBadge = document.getElementById('txtUnsavedBadge');
const txtModalLoading = document.getElementById('txtModalLoading');
const txtModalContent = document.getElementById('txtModalContent');  // <pre>
const txtModalEditor  = document.getElementById('txtModalEditor');   // <textarea>
const txtDiffView     = document.getElementById('txtDiffView');
const diffOriginal    = document.getElementById('diffOriginal');
const diffCurrent     = document.getElementById('diffCurrent');
const fnrBar          = document.getElementById('fnrBar');
const fnrFind         = document.getElementById('fnrFind');
const fnrReplace      = document.getElementById('fnrReplace');
const fnrReplaceOne   = document.getElementById('fnrReplaceOne');
const fnrReplaceAll   = document.getElementById('fnrReplaceAll');
const fnrCount        = document.getElementById('fnrCount');
const tbEdit          = document.getElementById('tbEdit');
const tbDiff          = document.getElementById('tbDiff');
const tbFind          = document.getElementById('tbFind');
const tbSave          = document.getElementById('tbSave');
const tbCancel        = document.getElementById('tbCancel');
const saveToast       = document.getElementById('saveToast');

/* ── Modal state ──────────────────────────────────────────────── */
const modalState = {
  mode:         'view',       // 'view' | 'edit' | 'diff'
  originalText: '',           // text as fetched from server
  currentFile:  null,         // { pdfName, txtFilename }
  isDirty:      false,
  showingFnr:   false,
};

/* ── isDirty helper ───────────────────────────────────────────── */
function setDirty(dirty) {
  modalState.isDirty = dirty;
  txtUnsavedBadge.classList.toggle('visible', dirty);
  tbSave.disabled = !dirty;
}

/* ─────────────────────────────────────────────────────────────────
   applyModalMode(mode)
   Handles all DOM show/hide transitions between view, edit, diff.
───────────────────────────────────────────────────────────────── */
function applyModalMode(mode) {
  modalState.mode = mode;

  const isEdit = mode === 'edit';
  const isDiff = mode === 'diff';
  const isView = mode === 'view';

  // <pre> visible in view mode only
  txtModalContent.style.display = isView ? 'block' : 'none';

  // <textarea> visible in edit mode only (display:block to fill flex parent correctly)
  txtModalEditor.style.display  = isEdit ? 'block' : 'none';

  // Diff panel visible in diff mode only
  txtDiffView.classList.toggle('visible', isDiff);

  // Toolbar states
  tbEdit.classList.toggle('active', isEdit || isDiff);
  tbEdit.textContent = (isEdit || isDiff) ? '✏️ Stop Editing' : '✏️ Edit';

  tbDiff.disabled = isView;
  tbDiff.classList.toggle('active', isDiff);

  // Save / Cancel only visible while editing
  tbSave.style.display   = (isEdit || isDiff) ? '' : 'none';
  tbCancel.style.display = (isEdit || isDiff) ? '' : 'none';

  // Focus textarea when entering edit mode
  if (isEdit) {
    txtModalEditor.focus();
  }

  // Rebuild diff whenever entering diff mode
  if (isDiff) {
    renderDiff();
  }
}

/* ─────────────────────────────────────────────────────────────────
   openTxtModal(pdfName, txtFilename)
   Entry point — fetches text, resets state, shows modal.
───────────────────────────────────────────────────────────────── */
async function openTxtModal(pdfName, txtFilename) {
  // Reset state
  modalState.currentFile  = { pdfName, txtFilename };
  modalState.originalText = '';
  modalState.isDirty      = false;
  modalState.showingFnr   = false;

  // Reset UI to view mode
  applyModalMode('view');
  setDirty(false);
  fnrBar.classList.remove('visible');
  tbFind.classList.remove('active');
  fnrFind.value    = '';
  fnrReplace.value = '';
  fnrCount.textContent = '';

  txtModalTitle.textContent  = pdfName;
  txtModalContent.textContent = '';
  txtModalEditor.value        = '';
  txtModalLoading.style.display = 'block';
  txtModalContent.style.display = 'none';

  txtModal.style.display = 'flex';

  try {
    const res = await fetch(`/ocr-result/${encodeURIComponent(txtFilename)}`);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }
    const text = await res.text();
    modalState.originalText     = text;
    txtModalContent.textContent = text;
    txtModalEditor.value        = text;
    txtModalLoading.style.display = 'none';
    txtModalContent.style.display = 'block';
  } catch (err) {
    txtModalContent.textContent   = `❌ Could not load OCR text: ${err.message}`;
    txtModalContent.style.display = 'block';
    txtModalLoading.style.display = 'none';
  }
}

/* ─────────────────────────────────────────────────────────────────
   closeTxtModal()
   Guards against accidental close when there are unsaved changes.
───────────────────────────────────────────────────────────────── */
function closeTxtModal() {
  if (modalState.isDirty) {
    if (!confirm('You have unsaved changes. Close without saving?')) return;
  }
  txtModal.style.display = 'none';
  // Reset to view mode for next open
  applyModalMode('view');
  setDirty(false);
}

/* ─────────────────────────────────────────────────────────────────
   TOOLBAR — Edit toggle
───────────────────────────────────────────────────────────────── */
tbEdit.addEventListener('click', () => {
  const currently = modalState.mode;

  if (currently === 'view') {
    // Enter edit mode
    txtModalEditor.value = txtModalContent.textContent;
    applyModalMode('edit');
  } else {
    // Exit edit/diff — warn if dirty
    if (modalState.isDirty) {
      if (!confirm('Discard unsaved changes and return to view?')) return;
    }
    // Revert textarea to original
    txtModalEditor.value = modalState.originalText;
    setDirty(false);
    applyModalMode('view');

    // Hide find bar
    fnrBar.classList.remove('visible');
    tbFind.classList.remove('active');
    modalState.showingFnr = false;
  }
});

/* ── Textarea change → dirty tracking ─────────────────────────── */
txtModalEditor.addEventListener('input', () => {
  const dirty = txtModalEditor.value !== modalState.originalText;
  setDirty(dirty);

  // If diff panel is open, refresh it live
  if (modalState.mode === 'diff') {
    renderDiff();
  }

  // Update fnr match count if bar is open
  if (modalState.showingFnr) {
    updateFnrCount();
  }
});

/* ─────────────────────────────────────────────────────────────────
   TOOLBAR — Diff toggle
───────────────────────────────────────────────────────────────── */
tbDiff.addEventListener('click', () => {
  if (modalState.mode === 'diff') {
    // Return to edit mode
    applyModalMode('edit');
  } else {
    // Enter diff mode (textarea stays as backing store)
    applyModalMode('diff');
  }
});

/* ─────────────────────────────────────────────────────────────────
   DIFF RENDERER
   Line-by-line comparison of originalText vs current textarea.
   Removed lines shown in left pane, added lines in right pane,
   unchanged lines shown in both with no highlight.
───────────────────────────────────────────────────────────────── */
function renderDiff() {
  const origLines = modalState.originalText.split('\n');
  const currLines = txtModalEditor.value.split('\n');
  const maxLen    = Math.max(origLines.length, currLines.length);

  diffOriginal.innerHTML = '';
  diffCurrent.innerHTML  = '';

  for (let i = 0; i < maxLen; i++) {
    const origLine = origLines[i] ?? '';
    const currLine = currLines[i] ?? '';
    const changed  = origLine !== currLine;

    const origSpan = document.createElement('span');
    origSpan.textContent = origLine + '\n';
    if (changed) {
      // If original line is empty, it's an addition in the current text.
      origSpan.className = origLine === '' ? 'diff-line-added' : 'diff-line-changed';
    }
    diffOriginal.appendChild(origSpan);

    const currSpan = document.createElement('span');
    currSpan.textContent = currLine + '\n';
    if (changed) {
      // If current line is empty, this line was removed from the current text.
      currSpan.className = currLine === '' ? 'diff-line-removed' : 'diff-line-changed';
    }
    diffCurrent.appendChild(currSpan);
  }

  // Sync scroll between panes
  syncDiffScroll();
}

function syncDiffScroll() {
  const left  = diffOriginal;
  const right = diffCurrent;
  let syncing = false;

  const handler = (source, target) => () => {
    if (syncing) return;
    syncing = true;
    target.scrollTop = source.scrollTop;
    syncing = false;
  };

  left.onscroll  = handler(left, right);
  right.onscroll = handler(right, left);
}

/* ─────────────────────────────────────────────────────────────────
   TOOLBAR — Save
   PUT /processed-files/:txtFilename  with text/plain body
───────────────────────────────────────────────────────────────── */
tbSave.addEventListener('click', async () => {
  if (!modalState.currentFile) return;
  const { txtFilename } = modalState.currentFile;
  const newText = txtModalEditor.value;

  // Disable save while in flight
  tbSave.disabled   = true;
  tbSave.innerHTML  = '<span class="tb-spinner"></span>Saving…';

  try {
    const res = await fetch(`/processed-files/${encodeURIComponent(txtFilename)}`, {
      method:  'PUT',
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      body:    newText,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `Server responded with ${res.status}`);
    }

    // Update original baseline so diff & dirty tracking reflect saved state
    modalState.originalText     = newText;
    txtModalContent.textContent = newText;   // keep <pre> current
    setDirty(false);

    // Return to view mode
    applyModalMode('view');
    fnrBar.classList.remove('visible');
    tbFind.classList.remove('active');
    modalState.showingFnr = false;

    showSaveToast();
    console.log(`[upload.js] #248 Saved edits to ${txtFilename}`);
  } catch (err) {
    alert(`Save failed: ${err.message}`);
    console.error('[upload.js] Save failed:', err.message);
    // Re-enable save so user can retry
    setDirty(true);
  } finally {
    tbSave.innerHTML = '💾 Save';
  }
});

/* ─────────────────────────────────────────────────────────────────
   TOOLBAR — Cancel
───────────────────────────────────────────────────────────────── */
tbCancel.addEventListener('click', () => {
  if (modalState.isDirty) {
    if (!confirm('Discard all unsaved changes?')) return;
  }
  txtModalEditor.value = modalState.originalText;
  setDirty(false);
  applyModalMode('view');

  fnrBar.classList.remove('visible');
  tbFind.classList.remove('active');
  modalState.showingFnr = false;
});

/* ─────────────────────────────────────────────────────────────────
   TOOLBAR — Find & Replace toggle
───────────────────────────────────────────────────────────────── */
tbFind.addEventListener('click', () => {
  modalState.showingFnr = !modalState.showingFnr;
  fnrBar.classList.toggle('visible', modalState.showingFnr);
  tbFind.classList.toggle('active', modalState.showingFnr);

  if (modalState.showingFnr) {
    fnrFind.focus();
    updateFnrCount();
  } else {
    fnrCount.textContent = '';
  }
});

/* ─────────────────────────────────────────────────────────────────
   FIND & REPLACE LOGIC
   Operates on txtModalEditor.value. Works in both edit and diff
   mode (diff refreshes automatically after replacement).
───────────────────────────────────────────────────────────────── */
function getFnrRegex() {
  const term = fnrFind.value;
  if (!term) return null;
  try {
    return new RegExp(escapeRegex(term), 'g');
  } catch (_) {
    return null;
  }
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function updateFnrCount() {
  const regex   = getFnrRegex();
  const enabled = !!regex && txtModalEditor.value.length > 0;
  fnrReplaceOne.disabled = !enabled;
  fnrReplaceAll.disabled = !enabled;

  if (!regex) {
    fnrCount.textContent = '';
    return;
  }

  const matches = txtModalEditor.value.match(regex);
  const count   = matches ? matches.length : 0;
  fnrCount.textContent = count === 0
    ? 'No matches'
    : `${count} match${count !== 1 ? 'es' : ''}`;
}

fnrFind.addEventListener('input', updateFnrCount);

fnrReplaceOne.addEventListener('click', () => {
  const regex = getFnrRegex();
  if (!regex) return;

  const text = txtModalEditor.value;
  // Replace only the first occurrence
  const oneRegex = new RegExp(escapeRegex(fnrFind.value));
  const updated  = text.replace(oneRegex, fnrReplace.value);

  if (updated === text) return;

  txtModalEditor.value = updated;
  setDirty(updated !== modalState.originalText);
  updateFnrCount();
  if (modalState.mode === 'diff') renderDiff();
});

fnrReplaceAll.addEventListener('click', () => {
  const regex = getFnrRegex();
  if (!regex) return;

  const updated = txtModalEditor.value.replace(regex, fnrReplace.value);
  if (updated === txtModalEditor.value) return;

  txtModalEditor.value = updated;
  setDirty(updated !== modalState.originalText);
  updateFnrCount();
  if (modalState.mode === 'diff') renderDiff();
});

/* ─────────────────────────────────────────────────────────────────
   CLOSE BUTTON & BACKDROP & ESCAPE
───────────────────────────────────────────────────────────────── */
document.getElementById('txtModalCloseBtn')
  .addEventListener('click', closeTxtModal);

txtModal.addEventListener('click', e => {
  if (e.target === txtModal) closeTxtModal();
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && txtModal.style.display === 'flex') {
    closeTxtModal();
  }
});

/* ─────────────────────────────────────────────────────────────────
   SAVE TOAST
───────────────────────────────────────────────────────────────── */
function showSaveToast() {
  saveToast.classList.add('show');
  setTimeout(() => saveToast.classList.remove('show'), 2400);
}

/* ══════════════════════════════════════════════════════════════
   INIT
══════════════════════════════════════════════════════════════ */
(async () => {
  await loadProcessedFiles();
  connectProcessedFilesSSE();
})();
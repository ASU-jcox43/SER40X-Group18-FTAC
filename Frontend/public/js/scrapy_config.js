// ── DOM refs ────────────────────────────────────────────────────────────────
const municipalitySearch  = document.getElementById('municipalitySearch');
const municipalityLinkList = document.getElementById('municipalityLinkList');
const selectedConfig      = document.getElementById('selectedConfig');

// ── State ────────────────────────────────────────────────────────────────────
let activeMunicipality = null;

// ── Build sidebar HTML ───────────────────────────────────────────────────────
function buildSidebar() {
    municipalitySearch.innerHTML = `
        <div class="panel-header">
            Municipalities
            <span class="sc-muni-badge" id="muniBadge">0</span>
        </div>
        <div class="sc-sidebar-body">
            <div class="sc-search-wrap">
                <span class="sc-search-icon">⌕</span>
                <input type="text" id="muniFilterInput" placeholder="Filter municipalities...">
            </div>
            <p class="sc-section-label">All</p>
            <ul id="municipalityListAll"></ul>
            <p class="sc-no-results" id="scNoResults">No municipalities found</p>
        </div>
    `;
}

// ── Build right panel HTML ───────────────────────────────────────────────────
function buildRightPanel() {
    // Config card
    selectedConfig.innerHTML = `
        <div class="sc-card" id="configCard">
            <div class="panel-header">
                <span id="configCardTitle">Select a municipality</span>
                <div style="display:flex;gap:0.5rem;align-items:center">
                    <span class="sc-run-status" id="runStatus"></span>
                    <button class="sc-btn-run" id="runScraperBtn">▶ Run scraper</button>
                </div>
            </div>
            <div class="sc-card-body" id="configCardBody">
                <p style="font-family:'Inter',sans-serif;font-size:0.875rem;color:#aaa;">
                    Select a municipality from the list to view and edit its config.
                </p>
            </div>
        </div>
    `;

    // Links card
    municipalityLinkList.innerHTML = `
        <div class="sc-card" id="linksCard">
            <div class="panel-header">
                <span>Scraped links</span>
                <a id="exportLinksBtn" class="sc-btn-header" style="display:none">Export list</a>
            </div>
            <div class="sc-links-body" id="linksCardBody">
                <p style="font-family:'Inter',sans-serif;font-size:0.875rem;color:#aaa;">
                    Select a municipality to see its scraped links.
                </p>
            </div>
        </div>
    `;

    // Wire up run scraper button
    document.getElementById('runScraperBtn').addEventListener('click', async () => {
        if (!activeMunicipality) return;
        const statusEl = document.getElementById('runStatus');
        statusEl.textContent = 'Starting...';
        try {
            const res = await fetch(`http://localhost:8000/ingest-docs?municipality=${activeMunicipality}`, {
                method: 'POST'
            });
            statusEl.textContent = res.ok ? 'Scraper started' : 'Failed to start';
        } catch {
            statusEl.textContent = 'Error';
        }
        setTimeout(() => { statusEl.textContent = ''; }, 3000);
    });
}

// ── Load all municipalities on page load ─────────────────────────────────────
async function loadAllMunicipalities() {
    buildSidebar();
    buildRightPanel();

    const res = await fetch('http://localhost:8000/scrapy_config');
    const municipalities = await res.json();

    const list = document.getElementById('municipalityListAll');
    const badge = document.getElementById('muniBadge');
    const filterInput = document.getElementById('muniFilterInput');
    const noResults = document.getElementById('scNoResults');

    badge.textContent = municipalities.length;

    for (const muni of municipalities) {
        const li = document.createElement('li');
        li.textContent = muni['_id'].replace(/_/g, ' ');
        li.dataset.id = muni['_id'];
        li.addEventListener('click', () => selectMunicipality(muni['_id'], li));
        list.appendChild(li);
    }

    // Live filter
    filterInput.addEventListener('input', () => {
        const q = filterInput.value.toLowerCase().trim();
        let visible = 0;
        list.querySelectorAll('li').forEach(li => {
            const match = li.textContent.toLowerCase().includes(q);
            li.classList.toggle('sc-hidden', !match);
            if (match) visible++;
        });
        noResults.style.display = visible === 0 ? 'block' : 'none';
        list.style.display = visible === 0 ? 'none' : '';
    });
}

// ── Select a municipality ────────────────────────────────────────────────────
async function selectMunicipality(id, liEl) {
    activeMunicipality = id;

    // Update active state
    document.querySelectorAll('#municipalityListAll li').forEach(li => li.classList.remove('active'));
    liEl.classList.add('active');

    // Update config card title
    document.getElementById('configCardTitle').textContent =
        id.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) + ' — config';

    // Update export link
    const exportBtn = document.getElementById('exportLinksBtn');
    exportBtn.href = `http://localhost:8000/scrapy_config/export_output?municipality=${id}`;
    exportBtn.download = `${id}.csv`;
    exportBtn.style.display = '';

    // Fetch and render config form
    const configRes = await fetch(`http://localhost:8000/scrapy_config?municipality=${id}`);
    const configs = await configRes.json();
    const config = configs.find(c => c['_id'] === id) || {};
    renderConfigForm(id, config);

    // Fetch and render links
    const linksRes = await fetch(`http://localhost:8000/scrapy_config/output?municipality=${id}`);
    const links = await linksRes.json();
    renderLinks(id, links);
}

// ── Render config form ───────────────────────────────────────────────────────
function renderConfigForm(id, config) {
    const body = document.getElementById('configCardBody');

    const NESTED_KEYS = ['layer_filter', 'next_page_filter', 'name_filter', 'number_filter', 'year_filter'];
    const SKIP_KEYS   = ['_id', 'update_at'];

    const form = document.createElement('form');
    form.id = 'scrapyConfigForm';
    form.noValidate = true;

    const grid = document.createElement('div');
    grid.className = 'sc-fields-grid';

    for (const [key, value] of Object.entries(config)) {
        if (SKIP_KEYS.includes(key)) continue;

        const isNested = NESTED_KEYS.includes(key) && value && typeof value === 'object' && !Array.isArray(value);
        const isArray  = Array.isArray(value);
        const isBool   = typeof value === 'boolean';

        const field = document.createElement('div');
        field.className = isNested || isArray ? 'sc-field full' : 'sc-field';

        const label = document.createElement('label');
        label.htmlFor = key;
        label.textContent = key.replace(/_/g, ' ');
        field.appendChild(label);

        if (isNested) {
            const nested = document.createElement('div');
            nested.className = 'sc-nested';
            for (const [subKey, subVal] of Object.entries(value)) {
                const subField = document.createElement('div');
                subField.className = 'sc-field';
                const subLabel = document.createElement('label');
                subLabel.htmlFor = `${key}-${subKey}`;
                subLabel.textContent = subKey;
                const subInput = document.createElement('input');
                subInput.type = 'text';
                subInput.id = `${key}-${subKey}`;
                subInput.name = `${key}-${subKey}`;
                subInput.value = subVal || '';
                subField.appendChild(subLabel);
                subField.appendChild(subInput);
                nested.appendChild(subField);
            }
            field.appendChild(nested);
        } else if (isArray) {
            const input = document.createElement('input');
            input.type = 'text';
            input.id = key;
            input.name = key;
            input.value = value.join(', ');
            field.appendChild(input);
        } else if (isBool) {
            const row = document.createElement('div');
            row.className = 'sc-checkbox-row';
            const cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.id = key;
            cb.name = key;
            cb.checked = value;
            const span = document.createElement('span');
            span.textContent = 'Enabled';
            row.appendChild(cb);
            row.appendChild(span);
            field.appendChild(row);
        } else {
            const input = document.createElement('input');
            input.type = typeof value === 'number' ? 'number' : 'text';
            input.id = key;
            input.name = key;
            input.value = value ?? '';
            if (typeof value === 'number') input.style.width = '80px';
            field.appendChild(input);
        }

        grid.appendChild(field);
    }

    form.appendChild(grid);

    const divider = document.createElement('hr');
    divider.className = 'sc-form-divider';
    form.appendChild(divider);

    const saveRow = document.createElement('div');
    saveRow.className = 'sc-save-row';

    const saveBtn = document.createElement('button');
    saveBtn.type = 'submit';
    saveBtn.className = 'sc-btn-save';
    saveBtn.textContent = 'Save config';

    const confirmation = document.createElement('p');
    confirmation.className = 'sc-confirmation';
    confirmation.textContent = 'Config saved';

    saveRow.appendChild(saveBtn);
    saveRow.appendChild(confirmation);
    form.appendChild(saveRow);

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = collectFormData(form, config);
        await fetch(`http://localhost:8000/scrapy_config?municipality=${id}`, {
            method: 'PUT',
            headers: { 'Content-type': 'application/json' },
            body: JSON.stringify(data)
        });
        confirmation.style.display = 'inline-block';
        setTimeout(() => { confirmation.style.display = 'none'; }, 2500);
    });

    body.innerHTML = '';
    body.appendChild(form);
}

// ── Collect form data back into the right shape ──────────────────────────────
function collectFormData(form, originalConfig) {
    const NESTED_KEYS = ['layer_filter', 'next_page_filter', 'name_filter', 'number_filter', 'year_filter'];
    const SKIP_KEYS   = ['_id', 'update_at'];
    const result = {};

    for (const [key, value] of Object.entries(originalConfig)) {
        if (SKIP_KEYS.includes(key)) continue;

        if (NESTED_KEYS.includes(key) && value && typeof value === 'object' && !Array.isArray(value)) {
            result[key] = {};
            for (const subKey of Object.keys(value)) {
                const el = form.querySelector(`#${key}-${subKey}`);
                result[key][subKey] = el ? el.value : value[subKey];
            }
        } else if (Array.isArray(value)) {
            const el = form.querySelector(`#${key}`);
            result[key] = el ? el.value.split(',').map(s => s.trim()).filter(Boolean) : value;
        } else if (typeof value === 'boolean') {
            const el = form.querySelector(`#${key}`);
            result[key] = el ? el.checked : value;
        } else if (typeof value === 'number') {
            const el = form.querySelector(`#${key}`);
            result[key] = el ? Number(el.value) : value;
        } else {
            const el = form.querySelector(`#${key}`);
            result[key] = el ? el.value : value;
        }
    }

    return result;
}

// ── Render links list ────────────────────────────────────────────────────────
function renderLinks(municipality, links) {
    const body = document.getElementById('linksCardBody');
    body.innerHTML = '';

    if (links && links.length > 0) {
        for (const link of links) {
            body.appendChild(makeLinkItem(municipality, link));
        }
    }

    // Always-visible add row
    const addRow = document.createElement('div');
    addRow.className = 'sc-add-row';

    const addInput = document.createElement('input');
    addInput.type = 'text';
    addInput.placeholder = 'Paste a link to add...';

    const addBtn = document.createElement('button');
    addBtn.type = 'button';
    addBtn.textContent = 'Add link';
    addBtn.addEventListener('click', async () => {
        const link = addInput.value.trim();
        if (!link) return;
        const res = await fetch(
            `http://localhost:8000/scrapy_config/output?municipality=${municipality}&link=${encodeURIComponent(link)}`,
            { method: 'POST', headers: { 'Content-type': 'application/json' } }
        );
        if (res.ok) {
            const body2 = await res.json();
            addInput.value = '';
            addRow.insertAdjacentElement('beforebegin', makeLinkItem(municipality, body2['new_link']));
        }
    });

    addRow.appendChild(addInput);
    addRow.appendChild(addBtn);
    body.appendChild(addRow);
}

// ── Make a single link list item ─────────────────────────────────────────────
function makeLinkItem(municipality, link) {
    const item = document.createElement('div');
    item.className = 'sc-link-item';

    const maxLen = 60;
    const anchor = document.createElement('a');
    anchor.href = link;
    anchor.title = link;
    anchor.textContent = link.length > maxLen
        ? `${link.slice(0, maxLen / 2)}...${link.slice(link.length - maxLen / 2 + 3)}`
        : link;

    const removeBtn = document.createElement('button');
    removeBtn.className = 'sc-btn-remove';
    removeBtn.textContent = 'Remove';
    removeBtn.addEventListener('click', async () => {
        const res = await fetch(
            `http://localhost:8000/scrapy_config/output?municipality=${municipality}&link=${encodeURIComponent(link)}`,
            { method: 'DELETE', headers: { 'Content-type': 'application/json' } }
        );
        if (res.ok) item.remove();
    });

    item.appendChild(anchor);
    item.appendChild(removeBtn);
    return item;
}

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadAllMunicipalities);
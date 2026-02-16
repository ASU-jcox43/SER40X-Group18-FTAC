// Province abbreviation → full name mapping
const provinceMap = {
  ON: "Ontario",
  BC: "British Columbia",
  AB: "Alberta",
  MB: "Manitoba",
  NB: "New Brunswick",
  NL: "Newfoundland and Labrador",
  NS: "Nova Scotia",
  PE: "Prince Edward Island",
  QC: "Quebec",
  SK: "Saskatchewan",
  YT: "Yukon",
  NT: "Northwest Territories",
  NU: "Nunavut"
};

// Show specific page
function showPanel(panelId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const selected = document.getElementById(panelId + 'Page');
  if (selected) selected.classList.add('active');
}

// Toggle right panel
function toggleDetailsPanel() {
  document.getElementById("detailsPanel").classList.toggle("hidden");
}

// Toggle individual sections
function toggleSection(button) {
  const section = button.parentElement;
  section.classList.toggle('open');
  //button.closest('.detail-section').classList.toggle('open');
}

// Header links
document.querySelectorAll('.header-nav a').forEach(link => {
  link.addEventListener('click', e => {
    if (link.hasAttribute('data-external')) return;
    e.preventDefault();
    const target = link.dataset.target;
    if (target) showPanel(target);
  });
});

// Global data
let municipalities = [];

// Load JSON data dynamically
document.addEventListener("DOMContentLoaded", async () => {
  try {
    const indexRes = await fetch("testdata/index.json");
    const indexData = await indexRes.json();

    // Fetch all municipalities listed in index.json
    const requests = indexData.municipalities.map(file =>
      fetch(`testdata/${file}`).then(res => res.json()) // remove extra .json if present
    );

    municipalities = await Promise.all(requests);
    renderTable(municipalities);
  } catch (err) {
    console.error("Failed to load test data:", err);
  }

  // Add sort change listener
  document.getElementById("sortOrder").addEventListener("change", applyFilters);
});

// Capitalize
function capitalize(str) {
  return (str || '').replace(/\b\w/g, c => c.toUpperCase());
}

// Render table
function renderTable(data) {
  const tbody = document.getElementById("jurisdictionBody");
  tbody.innerHTML = "";

  // Sort municipalities by score descending (highest score first)
  const sortedData = [...data].sort((a, b) => {
    const scoreA = a.friendlinessScore?.Score ?? 0;
    const scoreB = b.friendlinessScore?.Score ?? 0;
    return scoreB - scoreA; // highest first
  });

  sortedData.forEach((m, index) => {
    const row = document.createElement("tr");

    const score = m.friendlinessScore?.Score ?? 0;

    const provinceAbbrev = getProvinceAbbreviation(m.province); // returns ON, BC, etc.

    row.dataset.province = provinceAbbrev;
    row.dataset.score = score;
    row.dataset.business = m.fb_type?.trim().toLowerCase() ?? '';

    row.innerHTML = `
      <td>${index + 1}</td>   <!-- rank is now based on sorted order -->
      <td>${m.city ?? ''}</td>
      <td class="score">${score.toFixed(1)}</td>
      <td>${capitalize(m.fb_type)}</td>
    `;

    row.addEventListener("click", () => showDetails(m));
    tbody.appendChild(row);
  });
}


// Handle "ALL" checkboxes
document.addEventListener("DOMContentLoaded", () => {
  // Province ALL checkbox
  const provinceAll = document.querySelector('#province input[value="ALL"]');
  provinceAll.addEventListener('change', () => {
    const checked = provinceAll.checked;
    document.querySelectorAll('#province input:not([value="ALL"])')
            .forEach(cb => cb.checked = checked);
  });

  // Business Type ALL checkbox
  const businessAll = document.querySelector('#businessType input[value="ALL"]');
  businessAll.addEventListener('change', () => {
    const checked = businessAll.checked;
    document.querySelectorAll('#businessType input:not([value="ALL"])')
            .forEach(cb => cb.checked = checked);
  });
});

// Apply filters + sorting
function applyFilters() {
  const minScore = parseFloat(document.getElementById("minScore").value || 0);
  const sortOrder = document.getElementById("sortOrder").value;

  // Selected provinces (ignore ALL)
  const selectedProvinces = Array.from(
    document.querySelectorAll("#province input:checked:not([value='ALL'])")
  ).map(cb => cb.value);

  // Selected business types (ignore ALL)
  const selectedBusiness = Array.from(
    document.querySelectorAll("#businessType input:checked:not([value='ALL'])")
  ).map(cb => cb.value.toLowerCase());

  const tbody = document.getElementById("jurisdictionBody");
  let rows = Array.from(tbody.querySelectorAll("tr"));

  // Filter rows
  rows.forEach(row => {
    const rowProvince = row.dataset.province || '';
    const rowBusiness = (row.dataset.business || '').trim().toLowerCase();
    const rowScore = parseFloat(row.dataset.score) || 0;

    // If nothing is checked for a filter, treat it as "match all"
    const matchesProvince = selectedProvinces.length === 0 || selectedProvinces.includes(rowProvince);
    const matchesBusiness = selectedBusiness.length === 0 || selectedBusiness.includes(rowBusiness);
    const matchesScore = rowScore >= minScore;

    row.style.display = (matchesProvince && matchesBusiness && matchesScore) ? "" : "none";
  });

  // Re-rank visible rows
  let visibleRows = rows.filter(r => r.style.display !== "none");

  // Sort visible rows if sortOrder is selected
  if (sortOrder) {
    visibleRows.sort((a, b) => {
      const scoreA = parseFloat(a.dataset.score) || 0;
      const scoreB = parseFloat(b.dataset.score) || 0;
      if (sortOrder === "high-to-low") return scoreB - scoreA;
      if (sortOrder === "low-to-high") return scoreA - scoreB;
      return 0;
    });
  }

  visibleRows.forEach((row, index) => {
    row.querySelector("td").textContent = index + 1; // update rank
    tbody.appendChild(row);
  });
}

// Show details
// Show details
function showDetails(m) {
  const panel = document.getElementById("detailsPanel");
  panel.classList.remove("hidden");

  // Header info
  document.getElementById("municipalityName").textContent =
    m.city ?? "Unknown";

  document.getElementById("municipalityProvince").textContent =
    getProvinceAbbreviation(m.province);

  /* SUMMARY */
  const summaryEl = document.querySelector(
    "#detailsPanel .detail-section:nth-of-type(2) .collapse-content p"
  );

  if (summaryEl) {
    const score = m.friendlinessScore?.Score ?? 0;
    const indexLabel = m.friendlinessScore?.["Friendliness Index"] ?? "N/A";

    summaryEl.innerText = `
Friendliness Score: ${score.toFixed(1)}
Index: ${indexLabel}

Population: ${m.population?.toLocaleString() ?? "N/A"}
Median Income: $${m.income?.toLocaleString() ?? "N/A"}
Minimum Wage: ${m.min_wage ?? "N/A"}
    `.trim();
  }

  /* KEY REQUIREMENTS */
  const reqList = document.getElementById("requirementsList");
  if (reqList) {
    reqList.innerHTML = "";

    if (m.contacts && m.contacts.length > 0) {
      m.contacts.forEach(contact => {
        const li = document.createElement("li");
        li.textContent = contact.Department;
        reqList.appendChild(li);
      });
    } else {
      reqList.innerHTML = "<li>No requirements available</li>";
    }
  }

  /* SCORE BREAKDOWN */
  const scoreList = document.getElementById("scoreBreakdownList");
  if (scoreList) {
    scoreList.innerHTML = "";

    const breakdown = m.friendlinessScoreBreakdown || {};

    Object.entries(breakdown).forEach(([section, data]) => {
      const li = document.createElement("li");

      li.innerHTML =
        `<strong>${section}</strong>: ${data.Percentage} — ${data["Friendliness Index"]}`;

      scoreList.appendChild(li);
    });
  }
}

function getProvinceAbbreviation(fullName) {
  // create reverse mapping once
  const reverseProvinceMap = Object.fromEntries(
    Object.entries(provinceMap).map(([abbr, full]) => [full.toLowerCase(), abbr])
  );
  return reverseProvinceMap[fullName?.toLowerCase()] || "Unknown";
}

/* Upload PDF functionality */
document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("uploadForm");
  if (!form) return; // prevents running on non-upload pages

  const input = document.getElementById("pdfInput");
  const uploadBtn = document.getElementById("uploadBtn");
  const status = document.getElementById("status");
  const fileName = document.getElementById("fileName");

  input.addEventListener("change", () => {
    const file = input.files[0];

    if (!file) return;

    if (file.type !== "application/pdf") {
      status.textContent = "Only PDF files are allowed.";
      input.value = "";
      uploadBtn.disabled = true;
      fileName.textContent = "";
      return;
    }

    fileName.textContent = "Selected: " + file.name;
    status.textContent = "";
    uploadBtn.disabled = false;
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    status.textContent = "Uploading...";

    try {
      const response = await fetch("/upload", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        status.textContent = "Upload successful!";
        form.reset();
        uploadBtn.disabled = true;
        fileName.textContent = "";
      } else {
        status.textContent = "Upload failed.";
      }
    } catch {
      status.textContent = "Server error.";
    }
  });
});


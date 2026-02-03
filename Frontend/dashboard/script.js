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
  document.getElementById('detailsPanel').classList.toggle('collapsed');
}

// Toggle individual sections
function toggleSection(button) {
  button.closest('.detail-section').classList.toggle('open');
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

  data.forEach((m, index) => {
    const row = document.createElement("tr");

    const score = m.friendlinessScore?.Score ?? 0;
    row.dataset.province = m.province?.trim() ?? '';
    row.dataset.score = score;
    row.dataset.business = m.fb_type?.trim() ?? '';

    row.innerHTML = `
      <td>${index + 1}</td>
      <td>${m.city ?? ''}</td>
      <td class="score">${score.toFixed(1)}</td>
      <td>${capitalize(m.fb_type)}</td>
    `;

    row.addEventListener("click", () => showDetails(m));
    tbody.appendChild(row);
  });
}

// Apply filters + sorting
function applyFilters() {
  const provinceAbbrev = document.getElementById("province").value; // e.g., "ON"
  const minScore = parseFloat(document.getElementById("minScore").value || 0);
  const businessType = (document.getElementById("businessType").value || '').trim().toLowerCase();
  const sortOrder = document.getElementById("sortOrder").value;

  const tbody = document.getElementById("jurisdictionBody");
  let rows = Array.from(tbody.querySelectorAll("tr"));

  rows.forEach(row => {
    const rowProvince = row.dataset.province || '';
    const rowScore = parseFloat(row.dataset.score) || 0;
    const rowBusiness = (row.dataset.business || '').trim().toLowerCase();

    const matchesProvince = !provinceAbbrev || rowProvince === provinceMap[provinceAbbrev];
    const matchesScore = rowScore >= minScore;
    const matchesBusiness = !businessType || rowBusiness === businessType;

    row.style.display = matchesProvince && matchesScore && matchesBusiness ? "" : "none";
  });

  // Sort only visible rows
  if (sortOrder) {
    rows = rows.filter(r => r.style.display !== "none");

    rows.sort((a, b) => {
      const scoreA = parseFloat(a.dataset.score) || 0;
      const scoreB = parseFloat(b.dataset.score) || 0;
      if (sortOrder === "high-to-low") return scoreB - scoreA;
      if (sortOrder === "low-to-high") return scoreA - scoreB;
      return 0;
    });

    rows.forEach(row => tbody.appendChild(row));
  }
}

// Show details
function showDetails(m) {
  const summary = document.querySelector(".detail-section.open .collapse-content p");
  if (!summary) return;

  const score = m.friendlinessScore?.Score ?? 0;
  const indexLabel = m.friendlinessScore?.["Friendliness Index"] ?? 'N/A';

  summary.innerText = `
${m.city ?? 'Unknown'}, ${m.province ?? 'Unknown'}

Friendliness Score: ${score.toFixed(1)}
Index: ${indexLabel}

Population: ${m.population?.toLocaleString() ?? 'N/A'}
Median Income: $${m.income?.toLocaleString() ?? 'N/A'}
Minimum Wage: ${m.min_wage ?? 'N/A'}
  `.trim();
}

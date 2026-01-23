const reports = [];
const selected = new Set();

async function loadReports() {
    const res = await fetch("http://localhost:8000/Frontend/list-reports");
    const data = await res.json();

    reports.length = 0;
    reports.push(...data);

    renderReports();
}

function renderReports(filter = "") {
    const list = document.getElementById("reportList");
    list.innerHTML = "";
    reports
        .filter(r => r.name.toLowerCase().includes(filter.toLowerCase()))
        .forEach(r => {
            const li = document.createElement("li");
            li.innerHTML = `
                <label>
                    <input type="checkbox"
                       ${selected.has(r.id) ? "checked" : ""}
                       onchange="toggleReport('${r.id}')">
                    ${r.name}
                </label>
            `;
            list.appendChild(li);
        });
}

function toggleReport(id) {
    if (selected.has(id)) {
        selected.delete(id);
    }
    else {
        selected.add(id);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadReports();
    document.getElementById("search").addEventListener("input", e=> {
        renderReports(e.target.value);
    });
    document.getElementById("selectVisible").onclick = () => {
        const filter = document.getElementById("search").value.toLowerCase();
        reports
            .filter(r => r.name.toLowerCase().includes(filter))
            .forEach(r => selected.add(r.id));
        renderReports(filter);
    };
    document.getElementById("downloadSelected").onclick = async () => {
        if (selected.size === 0) {
            alert("No reports selected");
            return;
        }
        const res = await fetch("http://localhost:8000/Frontend/download-selected", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify([...selected])
        });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "selected_reports.zip";
        a.click();
        window.URL.revokeObjectURL(url);
    };
    document.getElementById("clearSelection").onclick = () => {
        selected.clear();
        renderReports(document.getElementById("search").value);
    };
    const form = document.getElementById('reportForm');
    const loadingDiv = document.getElementById('loading');
    const output = document.getElementById('reportOutput');
    const downloadForm = document.getElementById('downloadForm');

    downloadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        window.location.assign("http://localhost:8000/Frontend/download-reports");
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        output.value = "";
        loadingDiv.style.display = "block";

        try {
            const response = await fetch("http://localhost:8000/Frontend/generate-report", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
            });

            const results = await response.json();
            let html = "";

            results.forEach((report, index) => {
                html += `Report ${index + 1} Generated:\n`;
                html += `${report.filename}\n\n`;
            });

            output.value = html

            } catch (err) {
                output.value = "Error generating the reports.";
                console.error(err);
            } finally {
                loadingDiv.style.display = "none";
            }
        });
});
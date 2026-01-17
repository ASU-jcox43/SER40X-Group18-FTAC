document.addEventListener('DOMContentLoaded', () => {
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
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('reportForm');
    const loadingDiv = document.getElementById('loading');
    const output = document.getElementById('reportOutput');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        output.value = "";
        loadingDiv.style.display = "block";

        let formEntries = Object.fromEntries(new FormData(form));
        let reqBody = JSON.stringify({
            pdf: formEntries["reportPDF"]
        });

        try {
            let response = await fetch("http://localhost:8000/Frontend/generate-report", {
            method: "POST",
            body: reqBody,
            headers: { "Content-type": "application/json; charset=UTF-8"}
            });

            let results = await response.json();
            let html = "";

            results.forEach((report, index) => {
                html += `Report ${index + 1}:\n`;
                if (report.docx) {
                    html += `Download Word: ${report.docx}\n`;
                }
                if (report.pdf) {
                    html += `Download PDF: ${report.pdf}\n`;
                }
                html += "\n";
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
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('crawlForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let formEntries = Object.fromEntries(new FormData(form));
        let reqBody = JSON.stringify({
            start_url: formEntries["startUrl"],
            layers: Number(formEntries["numLayers"]),
            get_pdfs: formEntries["getPdfs"],
            regex: formEntries["regexFilter"]
        });

        console.log(reqBody);
        
        let response = await fetch("http://localhost:8000/Frontend/ingest-docs", {
                method: "POST",
                body: reqBody,
                headers: {
                    "Content-type": "application/json; charset=UTF-8"
                }
        })

        let outputText = document.getElementById('output');
        outputText.innerHTML = await response.text()
        })})
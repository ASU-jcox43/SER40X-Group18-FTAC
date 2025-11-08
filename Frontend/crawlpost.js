document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('crawlForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let formEntries = Object.fromEntries(new FormData(form));
        console.log(formEntries);
        
        fetch("localhost", {
            method: "POST",
            body: JSON.stringify({
                start_url: formEntries["startUrl"],
                layers: Number(formEntries["numLayers"]),
                get_pdfs: formEntries["getPdfs"],
                regex: formEntries["regexFilter"]
            }),
            headers: {
                "Content-type": "application/json; charset=UTF-8"
            }
        }
    );})})
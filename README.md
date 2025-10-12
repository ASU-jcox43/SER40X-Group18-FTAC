1. Clone the Repository
First, clone this repository to your local machine:
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo

2. Set Up a Python Virtual Environment
To isolate the dependencies for this project, create and activate a Python virtual environment:
On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
On Windows:
python -m venv venv
.\venv\Scripts\activate

3. Install Python Dependencies
Once the virtual environment is active, install the required Python libraries:
pip install -r requirements.txt

4. Install External Dependencies
Tesseract (for OCR)

macOS:
brew install tesseract
sudo apt-get install tesseract-ocr

Windows:
Download the Tesseract installer from Tesseract GitHub releases
Follow the installation instructions for Windows.
Add the Tesseract installation directory to your system’s PATH.

Poppler (for PDF to Image Conversion)
macOS:
brew install poppler

Windows:
Download Poppler for Windows from Poppler for Windows
Extract the contents and add the bin/ directory to your system’s PATH.

5. Run the Project
python OCRProcessor.py

6. Output
The script will process each PDF in the specified folder and generate a JSON file with the extracted data. For text-based PDFs, it will extract and organize text into sections. For scanned PDFs, it will run OCR to extract text and organize the data similarly.
The JSON files will be saved with the same name as the original PDF but with a _ocr.json or _text.json suffix depending on the type of PDF.


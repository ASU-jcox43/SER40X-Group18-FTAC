from openai import OpenAI
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.errors import HttpError
import json
import os
import sys

with open("config.json", "r") as f:
    config = json.load(f)

OPENAI_API_KEY = config["openai_api_key"]
GOOGLE_CREDENTIALS_PATH = config["google_credentials_path"]
TEMPLATE_DOC_ID = "1iCxIX_jh0UlXpeDaOFr1WPXAdKRbO01-heCo22RiVGU"

client = OpenAI(api_key=OPENAI_API_KEY)

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive"
]

creds = service_account.Credentials.from_service_account_file(
    GOOGLE_CREDENTIALS_PATH,
    scopes=SCOPES
)

print("Using service account:", getattr(creds, "service_account_email", None))

docs = build("docs", "v1", credentials=creds)
drive = build("drive", "v3", credentials=creds)

try:
    template_doc = docs.documents().get(documentId=TEMPLATE_DOC_ID).execute()
    print("Template title:", template_doc.get("title"))
except HttpError as e:
    print("Failed to read template doc. HTTP error:", e)
    print("If this is a 403, double-check that the template is shared with the service account client_email.")
    sys.exit(1)

template_text = ""
for c in template_doc.get("body", {}).get("content", []):
    if "paragraph" in c:
        for e in c["paragraph"]["elements"]:
            template_text += e.get("textRun", {}).get("content", "")

path = os.path.join("..", "analysis_ready", "Toronto_Food_Trucks_Copied_And_Pasted.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

prompt = f"""
You are a report generator. Using the data below, fill the report template.
Keep formatting similar to the template structure.

TEMPLATE:
{template_text}

DATA:
{json.dumps(data, indent=2)}
"""

try:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You generate structured policy reports about municipal regulations."},
            {"role": "user", "content": prompt}
        ]
    )
except Exception as e:
    print("OpenAI request failed:", e)
    sys.exit(1)

report_text = response.choices[0].message.content

copy_body = {"name": "Toronto Food Trucks Summary Report - (generated)"}
try:
    copied_file = drive.files().copy(
        fileId=TEMPLATE_DOC_ID,
        body=copy_body,
        supportsAllDrives=True
    ).execute()
    new_doc_id = copied_file["id"]
    print("Created copy with ID:", new_doc_id)
except HttpError as e:
    print("Failed to copy template. HTTP error:", e)
    print("If the file is on a Shared Drive, ensure service account is a member or supportsAllDrives used by owner creds.")
    sys.exit(1)

try:
    docs.documents().batchUpdate(
        documentId=new_doc_id,
        body={"requests": [{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": 999999}}},
                             {"insertText": {"location": {"index": 1}, "text": report_text}}]}
    ).execute()
    print("✅ Report created:")
    print(f"https://docs.google.com/document/d/{new_doc_id}/edit")
except HttpError as e:
    print("Failed to write to the new doc. HTTP error:", e)
    sys.exit(1)

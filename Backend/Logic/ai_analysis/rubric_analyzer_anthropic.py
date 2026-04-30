import os
import anthropic

# This is the main work AI analysis part of the project using Anthropic Claude.
# The idea is similar to the previous OpenAI test analysis part, but this instead imports in the official prompt,
# which right now is being opened as text. It is read, and then it can be called with download_analysis.
# Give download analysis the document, and then a True or False if it is a file that needs to be read or just text
# that is already ready to be analyzed. Give it some time, then it will create a document in the Downloaded_Analyses
# folder. It uses your Anthropic key as set by your system, so for example, I have my key set in Windows so that it uses
# it without me having to put anything in the public code. For testing purposes, feel free to paste in your code plainly
# but just make sure it never sees the public access.

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-haiku-4-5"

# Guidance prompt text is loaded in here
with open("FTAC_Prompt2.txt", "r", encoding="utf-8") as prompt:
    SYSTEM_PROMPT = prompt.read()

def analyze(document_text: str):
    user_prompt = f"""
    DOCUMENT:
    --- DOCUMENT START ---
    {document_text}
    --- DOCUMENT END ---
    """

    response = client.messages.create(
        model=MODEL,
        max_tokens=8192,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
    )
    return response.content[0].text


def download_analysis(document, isFile):
    if (isFile):
        with open(document, 'r', encoding="utf-8") as file:
            file_content = file.read()
    else:
        file_content = document

    report = analyze(file_content)
    with open("C:/Users/Jacob/repos/SER40X/SER40X-Group18-FTAC/Backend/Logic/ai_analysis/Downloaded_Analyses/output.md", "w", encoding="utf-8") as file:
        file.write(report)


if __name__ == "__main__":
    file_path = "C:/Users/Jacob/repos/SER40X/SER40X-Group18-FTAC/Backend/test_documents/Calgary_Food_Trucks_Copied_And_Pasted.txt"
    download_analysis(file_path, True)

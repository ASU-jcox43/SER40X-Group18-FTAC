import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-haiku-4-5"

# Guidance prompt text is loaded in here
with open("FTAC_Prompt.txt", "r", encoding="utf-8") as prompt:
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


if __name__ == "__main__":
    file_path = "C:/Users/Jacob/repos/SER40X/SER40X-Group18-FTAC/Backend/test_documents/Calgary_Food_Trucks_Copied_And_Pasted.txt"
    with open(file_path, 'r', encoding="utf-8") as file:
        file_content = file.read()

    report = analyze(file_content)
    print(report)

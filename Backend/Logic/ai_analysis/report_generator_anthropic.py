import os
import json
import anthropic
from Backend.Logic.ai_analysis.rubric_analyzer_anthropic import analyze_and_format
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-3-5-sonnet-latest"

SYSTEM_PROMPT = """
You are a municipal regulatory analyst for food truck businesses.

You will receive JSON data containing keyword-extracted sentences from a legal document.

Your job is to output a markdown report in EXACTLY this format:

# Summary Report for {filename}
**Overall Score:** {x}%
---
## Overview
| Total Categories | Found | Missing |
...
## Category Status
...
## Key Findings
...
## Recommendations
...

Rules:
- Mark a category as Found only if its keyword_contexts entry has data
- Clean up extracted sentences into readable findings
- Never invent information not present in the data
"""

def AI_Generate_Report(analyze):
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages = [
            {
                "role": "user",
                "content": f"Here is the extracted data:\n\n{analyze}"
            }
        ]
    )
    
    print(response.content[0].text)

if __name__ == "__main__":
    # TODO: Feed web links
    docs = getAllExtractions()
    for doc in docs:
        AI_Generate_Report(doc.get("keyword_contexts"))
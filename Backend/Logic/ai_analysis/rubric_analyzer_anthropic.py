import os
import json
import anthropic

# TODO: export ANTHROPIC_API_KEY="keyfile"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-3-5-sonnet-latest"
RUBRIC_JSON = [
  {
    "question": "Does this local jurisdiction have a webpage or section containing food truck information?",
    "options": [
      {"label": "Dedicated food truck webpage", "points": 2},
      {"label": "Food truck section within broader page", "points": 1},
      {"label": "Only in bylaws or unrelated page", "points": 0},
      {"label": "No centralized information", "points": 0}
    ]
  },
  {
    "question": "Is there an easy-to-understand application checklist for food trucks?",
    "options": [
      {"label": "Checklist provided", "points": 2},
      {"label": "Application form includes checklist", "points": 1},
      {"label": "Form without checklist", "points": 0},
      {"label": "Form mentioned but not accessible", "points": 0},
      {"label": "No form found", "points": 0}
    ]
  },
  {
    "question": "Is there an operational guide for obtaining a food truck license?",
    "options": [
      {"label": "PDF guide available", "points": 1},
      {"label": "Guide webpage available", "points": 1},
      {"label": "No guide", "points": 0}
    ]
  },
  {
    "question": "Are bylaws clearly displayed and linked?",
    "options": [
      {"label": "Listed and linked", "points": 2},
      {"label": "Available via linked pages", "points": 1},
      {"label": "Listed but not linked", "points": 0},
      {"label": "Not linked or listed", "points": 0},
      {"label": "Not found", "points": 0}
    ]
  },
  {
    "question": "Are bylaws accessible (translation, screen reader support)?",
    "options": [
      {"label": "Accessible", "points": 1},
      {"label": "Not accessible", "points": 0}
    ]
  },
  {
    "question": "Are penalties clearly stated?",
    "options": [
      {"label": "Detailed with fines (specific to food trucks)", "points": 2},
      {"label": "Detailed (general or no fine values)", "points": 1},
      {"label": "Mentioned without detail", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },

  {
    "question": "Provincial business license information",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned with limited info", "points": 1},
      {"label": "No information", "points": 0}
    ]
  },
  {
    "question": "Provincial food business license",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned", "points": 1},
      {"label": "Not required", "points": 2},
      {"label": "No information", "points": 0}
    ]
  },
  {
    "question": "Municipal business license",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned", "points": 1},
      {"label": "Not required", "points": 2},
      {"label": "No information", "points": 0}
    ]
  },
  {
    "question": "Municipal food truck license",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned", "points": 1},
      {"label": "No information", "points": 0},
      {"label": "Not required", "points": 0}
    ]
  },

  {
    "question": "Are food trucks allowed curbside vending?",
    "options": [
      {"label": "Yes, unrestricted", "points": 2},
      {"label": "Yes, with restrictions", "points": 1},
      {"label": "No", "points": 0}
    ]
  },
  {
    "question": "On-street parking fees",
    "options": [
      {"label": "All fees waived", "points": 2},
      {"label": "Permit or recurring fee", "points": 1},
      {"label": "Metered parking", "points": 0},
      {"label": "Not permitted", "points": 0}
    ]
  },
  {
    "question": "Noise bylaw impact on operating hours",
    "options": [
      {"label": "More flexible than bylaws", "points": 2},
      {"label": "Equal to bylaws", "points": 1},
      {"label": "More restrictive", "points": 0}
    ]
  },
  {
    "question": "Traffic bylaw impact on operating hours",
    "options": [
      {"label": "More flexible than bylaws", "points": 2},
      {"label": "Equal to bylaws", "points": 1},
      {"label": "More restrictive", "points": 0}
    ]
  },
  {
    "question": "Max operating hours restriction",
    "options": [
      {"label": ">5 hours", "points": 2},
      {"label": "3–5 hours", "points": 1},
      {"label": "<3 hours", "points": 0}
    ]
  },
  {
    "question": "Restrictions on selling packaged goods (CPG)",
    "options": [
      {"label": "No restrictions", "points": 2},
      {"label": "Requires extra permit", "points": 1},
      {"label": "Restricted/prohibited", "points": 0}
    ]
  },
  {
    "question": "Private property operation",
    "options": [
      {"label": "Allowed unrestricted", "points": 2},
      {"label": "Allowed with restrictions", "points": 1},
      {"label": "Not allowed", "points": 0}
    ]
  },
  {
    "question": "Proximity restrictions to other food businesses",
    "options": [
      {"label": "No restrictions", "points": 2},
      {"label": "Limited in specific cases", "points": 1},
      {"label": "Restricted", "points": 0}
    ]
  },
  {
    "question": "Limits on number of food trucks",
    "options": [
      {"label": "No limits", "points": 2},
      {"label": "Limited by logistics (traffic/parking)", "points": 1},
      {"label": "Strict limits", "points": 0}
    ]
  },
  {
    "question": "Designated parking locations",
    "options": [
      {"label": "No restrictions", "points": 2},
      {"label": "Defined via map/list", "points": 1},
      {"label": "Unclear or restrictive", "points": 0}
    ]
  },

  {
    "question": "Food safety authority identified",
    "options": [
      {"label": "Named with links", "points": 2},
      {"label": "Named without links", "points": 1},
      {"label": "Not identified", "points": 0}
    ]
  },
  {
    "question": "Link to food safety authority provided",
    "options": [
      {"label": "Provided", "points": 2},
      {"label": "Mentioned only", "points": 1},
      {"label": "Not provided", "points": 0}
    ]
  },
  {
    "question": "Insurance requirements clarity",
    "options": [
      {"label": "Detailed beyond minimums", "points": 2},
      {"label": "Basic requirements listed", "points": 1},
      {"label": "Minimal mention", "points": 0}
    ]
  },
  {
    "question": "Interior (food prep) requirements",
    "options": [
      {"label": "Detailed on website", "points": 2},
      {"label": "Only in bylaws", "points": 1},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Exterior/perimeter requirements",
    "options": [
      {"label": "Detailed", "points": 2},
      {"label": "General/vague", "points": 1},
      {"label": "Unspecified", "points": 0}
    ]
  }
]

SYSTEM_PROMPT = """You are a strict legal analyst specializing in municipal regulations, \
bylaws, and permitting requirements for mobile food vendors and food truck operations in Canada. \
Your role is to review regulatory documents with precision and objectivity, \
identifying whether the document satisfies each rubric criterion exactly as written.

Guidelines:
- Answer each rubric criterion directly and without elaboration beyond what the document states.
- Do not infer, assume, or extrapolate information that is not explicitly present in the document.
- Use formal legal language. Avoid colloquialisms or subjective commentary.
- If a criterion is only partially addressed, state what is present and what is absent.
- If a criterion is entirely unaddressed, state: "Not addressed in the document."
- Cite specific sections, clauses, or language from the document where applicable.
- Do not deviate from the rubric criteria or introduce additional evaluation dimensions."""


def analyze(document_text: str) -> dict:
    user_prompt = f"""
    Evaluate the document using the provided rubric.

    For EACH rubric item:
    - Select EXACTLY ONE option from the provided options.
    - Return:
      - "selected_option": exact label
      - "points": numeric score
      - "justification": short explanation citing the document
    
    Rules:
    - You MUST choose one of the provided options exactly as written.
    - Do NOT invent new options.
    - If information is missing, choose the lowest applicable score.
    
    Return STRICT JSON in this format:
    {{
      "results": [
        {{
          "question": "...",
          "selected_option": "...",
          "points": 0,
          "justification": "..."
        }}
      ],
      "total_score": <sum of all points>
    }}
    
    RUBRIC:
    {json.dumps(RUBRIC_JSON, indent=2)}
    
    DOCUMENT:
    --- DOCUMENT START ---
    {document_text}
    --- DOCUMENT END ---
    """

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": user_prompt}
        ],
    )

    content = response.content[0].text

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        raise ValueError("Model did not return valid JSON:\n" + content)

    return result


def analyze_and_format(document_text: str) -> str:
    results = analyze(document_text)
    lines = ["=" * 72, "RUBRIC ANALYSIS REPORT", "=" * 72, ""]

    total = 0

    for i, item in enumerate(results["results"], start=1):
        lines.append(f"[{i}] {item['question']}")
        lines.append("-" * 72)
        lines.append(f"Selected: {item['selected_option']}")
        lines.append(f"Points: {item['points']}")
        lines.append(f"Justification: {item['justification']}")
        lines.append("")
        total += item["points"]

    lines.append("=" * 72)
    lines.append(f"TOTAL SCORE: {total}")
    lines.append("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":
    sample_document = """TODO: Insert document text here."""

    report = analyze_and_format(sample_document)
    print(report)
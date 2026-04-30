import os
from openai import OpenAI
import json

# This file is not planned on being used anymore, but I kept it because I wanted to test OpenAI vs Anthropic at one
# point, and it has the old rubric I used before getting the official one.
# It uses the OpenAI API to use the rubric to analyze using each question, then creates a response in a JSON formatted
# string of text.

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4.1-mini"
RUBRIC_JSON = [
  {
    "question": "Does this local jurisdiction have a webpage, or section of a webpage, containing information specific to food trucks or mobile food?",
    "options": [
      {"label": "Municipality hosts a dedicated webpage for Food Trucks", "points": 2},
      {"label": "Food Trucks are given their own section/sub-section on a municipal webpage with other aligned food business information", "points": 1},
      {"label": "Food Truck information only available via the bylaws or on a page that is unrelated to food businesses in general", "points": 0},
      {"label": "No centralized space given for Food Truck licensing information on municipal webpage", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction offer an easy-to-understand application checklist specifically for food trucks, located in the designated area for food truck information?",
    "options": [
      {"label": "Checklist for application given", "points": 2},
      {"label": "Application form provided, included a checklist", "points": 1},
      {"label": "Application form provided, without a checklist", "points": 0},
      {"label": "Application form mentioned, but not accessible", "points": 0},
      {"label": "Application form not found", "points": 0}
    ]
  },
  {
    "question": "Does this local jurisdiction offer an operational guide that provides clear and easy-to-understand instructions for new entrepreneurs on how to obtain a food truck license?",
    "options": [
      {"label": "PDF guide available", "points": 1},
      {"label": "Guide webpage available", "points": 1},
      {"label": "No guide", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction's website clearly display the bylaws that regulate the operation of food trucks, with direct links to the actual bylaws?",
    "options": [
      {"label": "Listed and linked", "points": 2},
      {"label": "Available via linked pages", "points": 1},
      {"label": "Listed but not linked", "points": 0},
      {"label": "Not linked or listed", "points": 0},
      {"label": "Not found", "points": 0}
    ]
  },
  {
    "question": "Are the bylaws on the local jurisdiction’s website presented in a way that supports accessibility, including features like language translation and compatibility with screen readers?",
    "options": [
      {"label": "Accessible", "points": 1},
      {"label": "Not accessible", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction clearly state the penalties for violating food truck bylaws, including specific fines, operating restrictions, or license suspensions, so that operators fully understand the consequences of non-compliance?",
    "options": [
      {"label": "Detailed with fines (specific to food trucks)", "points": 2},
      {"label": "Detailed (general or no fine values)", "points": 1},
      {"label": "Mentioned without detail", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Provincial business license (mandatory)",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned with limited info", "points": 1},
      {"label": "No information", "points": 0}
    ]
  },
  {
    "question": "Provincial food business license (uncommon)",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned", "points": 1},
      {"label": "Not required", "points": 2},
      {"label": "No information", "points": 0}
    ]
  },
  {
    "question": "Municipal business license (currently assessing how common) (NOTE: This is not a food truck license. There are some jurisdictions that require a general business license and a food truck OR food business license)",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned", "points": 1},
      {"label": "Not required", "points": 2},
      {"label": "No information", "points": 0}
    ]
  },
  {
    "question": "Municipal food business/food truck license (common)",
    "options": [
      {"label": "Detailed with links", "points": 2},
      {"label": "Mentioned", "points": 1},
      {"label": "No information", "points": 0},
      {"label": "Not required", "points": 0}
    ]
  },
  {
    "question": "Retail license for CPG (Consumer Packaged Goods) (uncommon)",
    "options": [
      {"label": "Information and requirements for this license are provided with relevant links", "points": 2},
      {"label": "Mentions appear of this license, but information is limited", "points": 1},
      {"label": "No information", "points": 0},
      {"label": "Not required", "points": 2}
    ]
  },
  {
    "question": "Are food trucks permitted to park on city streets to allow for curbside vending?",
    "options": [
      {"label": "Yes, unrestricted", "points": 2},
      {"label": "Yes, with restrictions", "points": 1},
      {"label": "No", "points": 0}
    ]
  },
  {
    "question": "What are the fees associated with occupying on-street parking spaces for food trucks in this jurisdiction?",
    "options": [
      {"label": "All fees waived", "points": 2},
      {"label": "Permit or recurring fee", "points": 1},
      {"label": "Metered parking", "points": 0},
      {"label": "Not permitted", "points": 0}
    ]
  },
  {
    "question": "Are there any noise bylaws that restrict the operating hours of food trucks?",
    "options": [
      {"label": "More flexible than bylaws", "points": 2},
      {"label": "Equal to bylaws", "points": 1},
      {"label": "More restrictive", "points": 0}
    ]
  },
  {
    "question": "Are there any traffic bylaws that restrict the operating hours or locations of food trucks?",
    "options": [
      {"label": "More flexible than bylaws", "points": 2},
      {"label": "Equal to bylaws", "points": 1},
      {"label": "More restrictive", "points": 0}
    ]
  },
  {
    "question": "If there are restrictions on the number of hours food trucks are permitted to operate in this jurisdiction, what are those specific time restrictions?",
    "options": [
      {"label": ">5 hours", "points": 2},
      {"label": "3–5 hours", "points": 1},
      {"label": "<3 hours", "points": 0}
    ]
  },
  {
    "question": "Are there any regulations or restrictions that limit or prohibit the sale of branded consumer packaged goods from food trucks?",
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
      {"label": "Not allowed", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Does this local jurisdiction allow food trucks to operate on private property?",
    "options": [
      {"label": "Yes, unrestricted", "points": 2},
      {"label": "Yes, with restrictions", "points": 1},
      {"label": "No, not permitted", "points": 0},
      {"label": "Unspecified", "points": 0},
    ]
  },
  {
    "question": "Are there regulations limiting how close a food truck can operate to other food service businesses?",
    "options": [
      {"label": "No limitations by proximity restrictions", "points": 2},
      {"label": "Limited by proximity requirements only in specific use cases", "points": 1},
      {"label": "Limited by proximity requirements", "points": 0},
      {"label": "Limited from operating in an entire geographic area", "points": 0},
    ]
  },
  {
    "question": "Are there regulations that restrict food trucks from operating near certain non-food service businesses, such as schools, churches, or hospitals?",
    "options": [
      {"label": "No limitations by proximity restrictions", "points": 2},
      {"label": "Limited by proximity requirements only in specific use cases", "points": 1},
      {"label": "Limited by proximity requirements", "points": 0},
      {"label": "Limited from operating in an entire geographic area", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Does this local jurisdiction limit the number of food trucks allowed to operate within a specific geographic area?",
    "options": [
      {"label": "No limitations on number of trucks in a given area", "points": 2},
      {"label": "Limitations are in line with traffic management, limited parking or noise bylaws", "points": 1},
      {"label": "The number of operators are limited in a given area", "points": 0},
      {"label": "Limited from operating in an entire geographic area", "points": 0},
      {"label": "The number of operators are limited in this jurisdiction", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Does this jurisdiction explicitly define designated parking locations for food trucks, either through a location list or a map?",
    "options": [
      {"label": "Not limited to designated parking spaces", "points": 2},
      {"label": "Limited to designated parking spaces provided on a map", "points": 1},
      {"label": "Limited to designated parking spaces defined via a written list of street locations", "points": 1},
      {"label": "Limited, but designated locations are not clearly defined", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Beyond obtaining permission from the property owner, are there any additional restrictions in place for food trucks operating on private property in this jurisdiction?",
    "options": [
      {"label": "Yes", "points": 0},
      {"label": "No", "points": 1},
      {"label": "Unspecified", "points": 0},
    ]
  },
  {
    "question": "Does the local jurisdiction specify the name of the local authority responsible for conducting food safety inspections and enforcing regulations for food trucks?",
    "options": [
      {"label": "Municipality names the local food & safety authority, providing links to that authoritities food safety requirements", "points": 2},
      {"label": "Municipality names the local health authority, without providing link to the authority or its requirements", "points": 1},
      {"label": "Municipality does not outline the health authority responsible for food safety inspection", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction provide a direct link to the website of the local authority responsible for food safety inspections and regulations for food trucks?",
    "options": [
      {"label": "Municipality names the local food & safety authority, providing links to that authoritities food safety requirements", "points": 2},
      {"label": "Municipality names the local health authority, without providing link to the authority or its requirements", "points": 1},
      {"label": "Municipality does not outline the health authority responsible for food safety inspection", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction clearly specify the insurance requirements for food trucks, including minimum liability limits, provisions for additional insured parties, and any other relevant insurance information?",
    "options": [
      {"label": "Municipality details insurance requirements, providing information regarding any requirements beyond minimum coverage", "points": 2},
      {"label": "Municipality provides some insurance requirements, including minimum coverage requirements", "points": 1},
      {"label": "Municipality states insurance is required, but provides no further details or information", "points": 0},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction provide specific guidelines regarding the physical requirements that food trucks must meet, such as vehicle design or equipment, to ensure safe and sanitary operations? NOTE: This question relates to the food preparation area - aka the INTERIOR of the truck.",
    "options": [
      {"label": "Requirements for Food Truck measurements or specifications outlined on municipal website", "points": 2},
      {"label": "Requirements for Food Truck measurements or specifications provided in municipal Bylaws", "points": 1},
      {"label": "Unspecified", "points": 0}
    ]
  },
  {
    "question": "Does the local jurisdiction provide specific guidelines regarding the physical requirements that food trucks must meet, such as vehicle design or equipment, to ensure safe and sanitary operations? NOTE: This question relates to the food preparation area - aka the INTERIOR of the truck.",
    "options": [
      {"label": "Exterior & perimeter requirements provided on municipal website, with detailed descriptions", "points": 2},
      {"label": "Exterior & perimeter requirements provided in municipal bylaws, with detailed descriptions", "points": 2},
      {"label": "Exterior & perimeter requirement mentioned on municipal website, with only vague or general descriptions (such as 'must be kept cleaned or in good condition' without description of how those terms are appraised)", "points": 1},
      {"label": "Exterior & perimeter requirement mentioned in municipal bylaws, with only vague or general descriptions (such as 'must be kept cleaned or in good condition' without description of how those terms are appraised)", "points": 0},
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

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

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
    file_path = "C:/Users/Jacob/repos/SER40X/SER40X-Group18-FTAC/Backend/test_documents/Calgary_Food_Trucks_Copied_And_Pasted.txt"
    with open(file_path, 'r', encoding="utf-8") as file:
        file_content = file.read()

    report = analyze_and_format(file_content)
    print(report)

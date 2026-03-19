import os
import json
import anthropic

# TODO: export ANTHROPIC_API_KEY="keyfile"

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-3-5-sonnet-latest"
RUBRIC: list[str] = []  # TODO: populate rubric lines here

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
- Do not deviate from the rubric criteria or introduce additional evaluation dimensions.
"""


def analyze(document_text: str, rubric: list[str] | None = None) -> dict:
    criteria = rubric if rubric is not None else RUBRIC

    if not criteria:
        raise ValueError("Rubric is empty. Populate RUBRIC or pass a rubric list.")

    rubric_text = "\n".join([f"{i+1}. {criterion}" for i, criterion in enumerate(criteria)])

    user_prompt = f"""
    Evaluate the following regulatory document against ALL rubric criteria.

    Return a JSON object where:
    - Each key is the EXACT rubric criterion text
    - Each value is the analysis result

    RUBRIC:
    {rubric_text}
    
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


def analyze_and_format(document_text: str, rubric: list[str] | None = None) -> str:
    results = analyze(document_text, rubric)
    lines = ["=" * 72, "RUBRIC ANALYSIS REPORT", "=" * 72, ""]

    for i, (criterion, finding) in enumerate(results.items(), start=1):
        lines.append(f"[{i}] CRITERION: {criterion}")
        lines.append("-" * 72)
        lines.append(f"FINDING:\n{finding}")
        lines.append("")

    lines.append("=" * 72)
    lines.append("END OF REPORT")
    lines.append("=" * 72)
    return "\n".join(lines)


if __name__ == "__main__":
    sample_document = """TODO: Insert document text here."""

    report = analyze_and_format(sample_document)
    print(report)
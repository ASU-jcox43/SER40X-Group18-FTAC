import json

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILEPATH = ROOT / "Logic" / "analysis_ready"
SCORE = ROOT / "Backend" / "Logic" / "scoring" / "friendliness_summary.json"
OUTPUT = ROOT / "Logic" / "reports" / "generated_reports"

def generate_report(file_path, score_path, output_path):
    # Open the extracted text and scoring files.
    file_path = Path(file_path)
    score_path = Path(score_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(score_path, "r", encoding="utf-8") as f:
        scores = json.load(f)

    # Get the file name to search for in the score summary.
    filename = Path(data.get("file", "unnamed file")).with_suffix(".json").name

    score = scores.get(filename, {}).get("foodtruck", "N/A")

    keyword_contexts = data.get("keyword_contexts", {})

    # Now using markdown, we just format with normal text and download as md.
    markdown = []
    markdown.append(f"# Summary Report for {data.get('file', 'unnamed file')}\n")
    markdown.append(f"**Overall Score:** {score}%\n")

    # We have to make the table manually with text, but it's pretty similar.
    markdown.append("## Category Status\n")
    markdown.append("| Category | Status |\n")
    markdown.append("| ---------|--------|\n")

    # Add each category with either a found or missing tag.
    for category, content in keyword_contexts.items():
        empty = (len(content) == 0)
        status = "Found" if not empty else "Missing"
        markdown.append(f"| {category.capitalize()} | {status} |\n")

    # For key findings, check if they are unique by checking the seen set and adding to it if it is new.
    markdown.append("\n## Key Findings\n")

    seen = set()

    for category, content in keyword_contexts.items():
        if not isinstance(content, dict):
            continue
        for items in content.values():
            if not isinstance(items, list):
                continue
            for line in items:
                if len(line.split()) < 4:
                    continue
                line = line.strip()
                if not line.endswith("."):
                    line += "."
                if line not in seen:
                    markdown.append(f"- {line.capitalize()}\n")
                    seen.add(line)

    # For now, recommendations are just finding more info about missing categories.
    markdown.append("\n## Recommendations\n")
    for category, content in keyword_contexts.items():
        if len(content) == 0:
            markdown.append(f"- Find more information for **{category}**.\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(markdown))

    print(f"Markdown saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    OUTPUT.mkdir(exist_ok=True)
    for file_path in FILEPATH.iterdir():
        output_path = OUTPUT / f"{file_path.stem}_Report.md"
        generate_report(file_path, SCORE, output_path)
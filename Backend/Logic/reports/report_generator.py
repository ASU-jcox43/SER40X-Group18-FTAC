from pathlib import Path
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions
from Backend.Logic.mongo_db.scoring_collection import getSummary

# OUTPUT = Path("Backend/Logic/reports/generated_reports")
BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "generated_reports"

def has_sentences(content):
    if not isinstance(content, list):
        return False
    return any(isinstance(item, dict) and isinstance(item.get("sentence"), str) for item in content)

def generate_report(data, scores, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get the file name to search for in the score summary.
    filename = Path(data.get("file", "unnamed file")).stem

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
        status = "Found" if has_sentences(content) else "Missing"
        markdown.append(f"| {category.capitalize()} | {status} |\n")

    # For key findings, check if they are unique by checking the seen set and adding to it if it is new.
    markdown.append("\n## Key Findings\n")

    seen = set()
    found_any = False

    for category, content in keyword_contexts.items():
        if not isinstance(content, list):
            continue
        for entry in content:
            if isinstance(entry, dict):
                line = entry.get("sentence")
            else:
                line = entry
            if not isinstance(line, str):
                continue
            line = line.strip()

            if len(line.split()) < 4:
                continue

            if not line.endswith("."):
                line += "."

            if line not in seen:
                markdown.append(f"- {line.capitalize()}\n")
                seen.add(line)
                found_any = True
        if not found_any:
            markdown.append("No key findings were extracted.\n")

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
    
    docs = getAllExtractions()
    scores = getSummary()
    
    for doc in docs:
        filename = Path(doc.get("file", "unknown")).stem
        output_path = OUTPUT / f"{filename}_Report.md"
        generate_report(doc, scores, output_path)
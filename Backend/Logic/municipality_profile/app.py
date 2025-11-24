from flask import Flask, render_template, request
from search_manager import load_profiles, search_profiles

app = Flask(__name__)

# Load profiles once at startup
profiles = load_profiles()

PROVINCES = [
    "Alberta",
    "British Columbia",
    "Manitoba",
    "New Brunswick",
    "Newfoundland and Labrador",
    "Nova Scotia",
    "Ontario",
    "Prince Edward Island",
    "Quebec",
    "Saskatchewan",
    "Northwest Territories",
    "Nunavut",
    "Yukon"
]

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    results = None
    sort_order = None  
    province = None
    min_score = None

    if request.method == "POST":
        province = request.form.get("province")
        min_score = request.form.get("minScore")
        min_score = float(min_score) if min_score else None
        sort_order = request.form.get("sortOrder")

        # Treat empty string or "all" as no filter
        if not province or province.lower() == "all":
            province = None

        results = search_profiles(profiles, min_score=min_score, province=province, sort_order=sort_order)
    
    return render_template("index.html", results=results, provinces=PROVINCES)

if __name__ == "__main__":
    app.run(debug=True)

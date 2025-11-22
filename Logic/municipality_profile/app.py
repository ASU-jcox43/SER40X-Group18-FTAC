from flask import Flask, render_template, request
from search_manager import load_profiles, search_profiles

app = Flask(__name__)

# Load profiles once at startup
profiles = load_profiles()

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        province = request.form.get("province")
        min_score = request.form.get("minScore")
        min_score = float(min_score) if min_score else None

        # Treat empty string or "all" as no filter
        if not province or province.lower() == "all":
            province = None

        results = search_profiles(profiles, min_score=min_score, province=province)
    
    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)

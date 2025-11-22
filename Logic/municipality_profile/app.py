from flask import Flask, render_template, request, jsonify
import search_manager

app = Flask(__name__)

# Load profiles once
profiles = search_manager.load_profiles()
provinces = sorted(list({p["Province"] for p in profiles if p["Province"]}))

@app.route("/")
def index():
    return render_template("index.html", provinces=provinces)

@app.route("/search", methods=["POST"])
def search():
    province = request.form.get("province")
    min_score = request.form.get("min_score")
    try:
        min_score = float(min_score) if min_score else None
    except ValueError:
        min_score = None
    results = search_manager.search_profiles(profiles, min_score=min_score, province=province)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)

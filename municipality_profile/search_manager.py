import json 
import pprint
from pathlib import Path

# Relevant json fields to search through 
RELEVANT_FIELDS = [
    "Geographic.City", "Province", "Geographic.Region",
    "friendlinessScore", "friendlinessScoreBreakdown",
    ]

def get_nested_data(data, path):
    keys = path.split(".")
    for k in keys:
        if isinstance(data, dict):
            data = data.get(k)
        else:
            return None
    return data

# Load all profiles
def load_profiles():
    profiles_dir = Path(__file__).parent / "profiles"
    profiles = []

    for file in profiles_dir.glob("*_profile.json"):
        with open(file, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    profiles.append(normalize_profile(item))
            else:
                profiles.append(normalize_profile(data))

    return profiles


def normalize_profile(data):
    geo = data.get("Geographic", {})
    city = geo.get("City")
    province = geo.get("Province") or data.get("Province")
    region = geo.get("Region")

    score = data.get("friendlinessScore")
    if isinstance(score, list) and score:
        score = score[0]
    elif isinstance(score, dict):
        pass
    else:
        score = {}

    score_value = score.get("Score") or score.get("Friendliness Score") or 0
    try: 
        score_value = float(score_value)
    except (ValueError, TypeError):
        score_value = 0.0

    breakdown = data.get("friendlinessScoreBreakdown")
    if isinstance(breakdown, list) and breakdown:
        breakdown = breakdown[0]

    return {
        "City": city,
        "Province": province,
        "Region": region,
        "Score": score_value,
        "Friendliness Index": score.get("Friendliness Index", ""),
        "Breakdown": breakdown
    }


# Search profiles based on specific criteria
def search_profiles(profiles, min_score=None, province=None, city=None, region=None):
    results = []

    for profile in profiles:
        if min_score is not None and profile["Score"] < min_score:
            continue
        if province is not None and profile["Province"] != province:
            continue
        if city is not None and profile["City"] != city:
            continue
        if region is not None and profile["Region"] != region:
            continue
        results.append(profile)

    return results

if __name__ == "__main__":
    print("Loading profiles...")
    profiles = load_profiles()

    # Print loading functionality
    #print("\nAll Profiles:")
    #pprint.pprint(profiles)

    # Print search functionality
    print ("\nSearching for profiles with friendliness score > 83:")
    results = search_profiles(profiles, min_score=83.0, province="Ontario")
    pprint.pprint(results)

    # Print Search by province functionality
    print("\nSearching for profiles in Ontario:")
    results = search_profiles(profiles, province="Ontario")
    pprint.pprint(results)
    
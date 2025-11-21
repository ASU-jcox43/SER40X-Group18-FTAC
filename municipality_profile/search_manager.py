import json 
import pprint
from pathlib import Path

# Relevant json fields to search through 
RELEVANT_FIELDS = [
    "friendlinessScore", "friendlinessScoreBreakdown",
    "Geographic.City", "Province", "Geographic.Region"
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
            # Filter for relevant json fields
            filtered = {key.replace(".", "_"): 
                        get_nested_data(data, key) for key in RELEVANT_FIELDS}
            profiles.append(filtered)

    return profiles


if __name__ == "__main__":
    print("Loading profiles...")
    profiles = load_profiles()

    print("\nAll Profiles:")
    pprint.pprint(profiles)


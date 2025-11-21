import json 
import pprint
from pathlib import Path


# Load all profiles

def load_profiles():
    profiles_dir = Path(__file__).parent / "profiles"
    profiles = []

    for file in profiles_dir.glob("*.json"):
        with open(file, "r") as f:
            data = json.load(f)
            profiles.append(data)

    return profiles


if __name__ == "__main__":
    print("Loading profiles...")
    profiles = load_profiles()

    print("\nAll Profiles:")
    pprint.pprint(profiles)


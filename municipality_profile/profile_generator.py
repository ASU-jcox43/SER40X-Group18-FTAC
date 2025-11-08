import os
import json
from datetime import datetime
from profile_manager import createMunicipalityProfile


def addProfile(**kwargs):
    profile = createMunicipalityProfile(**kwargs)
    # Save/update the profile

    save_path = load_existing_profile(profile)
    return save_path

def load_existing_profile(profile):
    city = profile["Geographic"]["City"]
    province = profile["Geographic"]["Province"]

    # folder path for profiles
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, "profiles")
    os.makedirs(folder_path, exist_ok=True)

    # Use city name as filename
    save_path = os.path.join(
        folder_path, f"{city.lower().replace(' ', '_')}_profile.json"
    )

    existing_profile = {}
    # Check if the file exists and load existing profile
    if os.path.exists(save_path):
        # Read existing data
        try:
            with open(save_path, "r", encoding="UTF-8") as file:
                data = file.read().strip()
                if data:
                    loaded = json.loads(data)
                    if isinstance(loaded, dict):
                        existing_profile = loaded
                    else:
                        print("Existing JSON is resetting.")
        except json.JSONDecodeError:
            # If file is empty or invalid JSON
            print("JSON decode error, resetting existing profile:")

    # Update changed values
    for key, value in profile.items():
        if key not in existing_profile or existing_profile[key] != value:
            existing_profile[key] = value
    print(f"Updated profile.")

    # Write updated data back to file
    with open(save_path, "w") as file:
        json.dump(existing_profile, file, indent=4)

    print(f"Profile for {city}, {province} saved to {save_path} successfully!")

if __name__ == "__main__":
    #load test data 
    with open("test_profile_data.json", "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    # timestamp automatically 
    test_data["last_updated"] = datetime.now().isoformat()

    addProfile(**test_data)
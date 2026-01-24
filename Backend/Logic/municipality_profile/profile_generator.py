import os
import json
from datetime import datetime
from Backend.Logic.municipality_profile.profile_manager import createMunicipalityProfile
from Backend.Logic.mongo_db.profile_collection import upsert_profile


def addProfile(**kwargs):
    profile = createMunicipalityProfile(**kwargs)
    # Save/update the profile

    upsert_profile(profile)
    print(f"Upserted profile for {profile['Geographic']['City']}")

def load_existing_profile(profile): # TODO: Delete later if MongoDB works
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
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(base_dir, "testData")

    for filename in os.listdir(test_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(test_dir, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                test_data = json.load(f)
            
            # timestamp automatically 
            test_data["last_updated"] = datetime.now().isoformat()

            addProfile(**test_data)
            print(f"Processed {filename}")
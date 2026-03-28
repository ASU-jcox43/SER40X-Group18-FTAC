import os
import json
from datetime import datetime
from Backend.Logic.municipality_profile.profile_manager import createMunicipalityProfile
from Backend.Logic.mongo_db.profile_collection import upsertProfile


def addProfile(**kwargs):
    profile = createMunicipalityProfile(**kwargs)
    # Save/update the profile

    upsertProfile(profile)
    print(f"Upserted profile for {profile['Geographic']['City']}")

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
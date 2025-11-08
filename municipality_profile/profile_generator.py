import os
import json
from datetime import datetime
from profile_manager import createMunicipalityProfile

def addProfile(
    name, fbType, city, province, 
        population, avgAge, community, income, 
        minWage, commTaxRates,
        lastUpdated
):
    # Add logic to ask for profile information
    profile = createMunicipalityProfile(
        name, fbType, city, province, 
        population, avgAge, community, income, 
        minWage, commTaxRates,
        lastUpdated
    )

    # folder path for profiles
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, "profiles")
    os.makedirs(folder_path, exist_ok=True)

     # Use city name as filename
    save_path = os.path.join(folder_path, f"{city.lower().replace(' ', '_')}_profile.json")

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
             print("JSON decode error — resetting existing profile:", e)

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
    # example values for testing
    name = "Jacob"
    fbType = "food truck"
    city = "Toronto"
    province = "Ontario"
    population = 2800000
    avgAge = 35
    community = "community"
    income = 600000
    minWage = 17.00
    commTaxRates = 0.20
    lastUpdated = datetime.now().isoformat()

    addProfile(
        name, fbType, city, province, 
        population, avgAge, community, income, 
        minWage, commTaxRates,
        lastUpdated
    )

import os
import json
from profile_manager import createMunicipalityProfile

def addProfile(
    name, city, province, population, age, community, income, minWage, commTaxRates
):
    # Add logic to ask for profile information
    profile = createMunicipalityProfile(
        name, city, province, population, age, community, income, minWage, commTaxRates
    )

    # folder path for profiles
    base_dir = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_dir, "profiles")
    os.makedirs(folder_path, exist_ok=True)

     # Use city name as filename
    save_path = os.path.join(folder_path, f"{city.lower().replace(' ', '_')}_profile.json")

    # Check if the file exists
    if os.path.exists(save_path):
        # Read existing data
        with open(save_path, "r") as file:
            try:
                profileJSON = json.load(file)
                if not isinstance(profileJSON, list):
                    profileJSON = []
            except json.JSONDecodeError:
                # If file is empty or invalid JSON
                profileJSON = []
    else:
        # If file doesn't exist, start with an empty list
        profileJSON = []

    # Append new profile (can be dict, list, etc.)
    profileJSON.append(profile)

    # Write updated data back to file
    with open(save_path, "w") as file:
        json.dump(profileJSON, file, indent=4)

    print(f"Profile for {city}, {province} saved to {save_path} successfully!")

if __name__ == "__main__":
    # example values for testing
    name = "Jacob"
    city = "Toronto"
    province = "Ontario"
    population = 2800000
    age = 35
    community = "community"
    income = 600000
    minWage = 17.00
    commTaxRates = 0.20

    addProfile(
        name, city, province, population, age, community, income, minWage, commTaxRates
    )

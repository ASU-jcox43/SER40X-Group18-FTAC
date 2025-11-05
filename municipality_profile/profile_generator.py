import os
import json
from datetime import datetime
from profile_manager import createMunicipalityProfile


def addProfile(
    name,
    fb_type,
    city,
    province,
    population,
    avgAge,
    ethnicity,
    houseSize,
    educationLevel,  # list of education levels
    income,
    min_wage,
    comm_tax_rates,
    last_updated,
    region,
    popSqMile,
    areaSqMiles,
    lat,
    long,
    adjMunicipalities,  # list of neighboring municipalities
):
    # Add logic to ask for profile information
    profile = createMunicipalityProfile(
        name,
        fb_type,
        city,
        province,
        population,
        avgAge,
        ethnicity,
        houseSize,
        educationLevel,  # list of education levels
        income,
        min_wage,
        comm_tax_rates,
        last_updated,
        region,
        popSqMile,
        areaSqMiles,
        lat,
        long,
        adjMunicipalities,  # list of neighboring municipalities
    )

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
            print("JSON decode error — resetting existing profile:")

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
    fb_type = "food truck"
    city = "Toronto"
    province = "Ontario"
    population = 2800000
    avgAge = 36.8
    ethnicityComposition = {
        "White": 65.0,
        "Hispanic": 10.0,
        "Filipino": 10.0,
        "Asian": 15.0,
    }
    houseSize = 2.8
    educationLevel = {
        "High School": 90.0,
        "College": 48.5,
    }
    income = 600000
    min_wage = 17.00
    comm_tax_rates = 0.20
    last_updated = datetime.now().isoformat()
    region = "Central Canada"
    popSqMile = 4750
    areaSqMiles = 40.2
    lat = 33.4
    long = -111.5
    adjMunicipalities = {"Phoenix", "Scottsdale", "Mesa"}

    addProfile(
        name,
        fb_type,
        city,
        province,
        population,
        avgAge,
        ethnicityComposition,
        houseSize,
        educationLevel,
        income,
        min_wage,
        comm_tax_rates,
        last_updated,
        region,
        popSqMile,
        areaSqMiles,
        lat,
        long,
        adjMunicipalities,
    )

import os
import json
from profile_manager import createMunicipalityProfile

SAVEPATH = os.path.join("..", "municipality_profile", "profiles.json")


def addProfile(name, province, population, age, income, community):
    # Add logic to ask for profile information
    profile = createMunicipalityProfile(
        name, province, population, age, income, community
    )

    # Check if the file exists
    if os.path.exists(SAVEPATH):
        # Read existing data
        with open(SAVEPATH, "r") as file:
            try:
                profileJSON = json.load(file)
            except json.JSONDecodeError:
                # If file is empty or invalid JSON
                profileJSON = []
    else:
        # If file doesn't exist, start with an empty list
        profileJSON = []

    # Append new profile (can be dict, list, etc.)
    profileJSON.append(profile)

    # Write updated data back to file
    with open(SAVEPATH, "w") as file:
        json.dump(profileJSON, file, indent=4)


if __name__ == "__main__":
    # example values for testing
    name = "Jacob"
    province = "Ontario"
    population = 2800000
    age = 35
    income = 600000
    community = "community"
    addProfile(name, province, population, age, income, community)

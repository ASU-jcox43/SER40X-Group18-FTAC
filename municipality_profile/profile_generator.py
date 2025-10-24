import os
from profile_manager import createProfile

SAVEPATH = os.path.join("..", "municipality_profile", "profiles.json")


def createMunicipalityProfile(name, province, population, age, income, community):
    # Add logic to ask for profile information
    profile = createProfile(name, province, population, age, income, community)

# example values for testing
name = "Jacob"
province = "Ontario"
population = 2,800,000
age = 35
income = 60,0000
community = "community"

if __name__ == "__main__":
    createMunicipalityProfile(name, province, population, age, income, community)

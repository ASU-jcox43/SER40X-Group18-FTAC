import os
from profile_manager import createProfile

SAVEPATH = os.path.join("..", "municipality_profile", "profiles.json")


def addProfile(name, province, population, age, income, community):
    # Add logic to ask for profile information
    profile = createProfile(name, province, population, age, income, community)


if __name__ == "__main__":
    addProfile("Jacob", "Toronto", 100, 50, 6000, "community")

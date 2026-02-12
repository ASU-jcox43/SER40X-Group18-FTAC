from .comparison_util import getMunicipalityProfiles, processSelections

# Display list of profiles
def displayProfiles():
    profiles = getMunicipalityProfiles()

    for i, profile in enumerate(profiles, start=1):
        city = profile["Geographic"]["City"]
        print(f"{i}. {city}")
        
# Waits for user's selection of profile
def getProfileSelections():
    while True:
        print("Choose two profiles to compare")
        
        selection1 = input("First Selection: ")
        selection2 = input("Second Selection: ")
        print()
        
        if processSelections(selection1, selection2):
            break

        print("Invalid Selection\n")

if __name__ == "__main__":
    displayProfiles()
    getProfileSelections()
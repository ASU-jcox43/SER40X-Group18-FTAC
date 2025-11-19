from comparison_util import getMunicipalityProfiles, readMunicipalityJson, processSelections

def displayProfiles():
    municipalityPaths = getMunicipalityProfiles()
    municipalityContent = readMunicipalityJson(municipalityPaths)
    
    print()
    for i, profileName in enumerate(municipalityContent.keys(), start=1):
        formatedProfileName = profileName.capitalize().replace("_profile", "")
        print(f"{i}. {formatedProfileName}")
        
def getProfileSelections():
    print("Choose two profiles to compare")
    
    selection1 = input("First Selection: ")
    selection2 = input("Second Selection: ")
    
    print(processSelections(selection1, selection2))

if __name__ == "__main__":
    displayProfiles()
    getProfileSelections()
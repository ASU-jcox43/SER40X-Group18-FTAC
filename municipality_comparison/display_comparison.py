from comparison_util import getMunicipalityProfiles, readMunicipalityJson, processSelections

def displayProfiles():
    municipalityPaths = getMunicipalityProfiles()
    municipalityContent = readMunicipalityJson(municipalityPaths)
    
    for i, profileName in enumerate(municipalityContent.keys(), start=1):
        formatedProfileName = profileName.capitalize().replace("_profile", "")
        print(f"{i}. {formatedProfileName}")
        
def getProfileSelections():
    result = False
    
    while result == False:
        print("Choose two profiles to compare")
        
        selection1 = input("First Selection: ")
        selection2 = input("Second Selection: ")
        print()
        
        result = processSelections(selection1, selection2)
        
        if result == False:
            print("Invalid Selection")
            print()

if __name__ == "__main__":
    displayProfiles()
    getProfileSelections()
from comparison_util import getMunicipalityProfiles, readMunicipalityJson 

def displayProfiles() :
    municipalityPaths = getMunicipalityProfiles()
    municipalityContent = readMunicipalityJson(municipalityPaths)
    
    print()
    for i, profileName in enumerate(municipalityContent.keys(), start=1):
        formatedProfileName = profileName.capitalize().replace("_profile", "")
        print(f"{i}. {formatedProfileName}")
    
if __name__ == "__main__":
    displayProfiles()
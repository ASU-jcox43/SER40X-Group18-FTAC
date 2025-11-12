import json
from pathlib import Path

# Folder containing JSON files
PROFILES_PATH = "../municipality_profile/profiles"

# Gets a list of municipality profile paths
def getMunicipalityProfiles():
    directory = Path(PROFILES_PATH)

    if not directory.exists():
        print(f"Error: The directory '{directory}' does not exist.")
        return []

    jsonFiles = list(directory.rglob("*.json"))
    
    if not jsonFiles:
        print("No JSON files found.")
    else:
        print(f"Found {len(jsonFiles)} JSON file(s):")
        for file in jsonFiles:
            print(f"{file}")

    return jsonFiles # Returns list of paths to each profile

# Reads each from the list of paths
def readMunicipalityJson(municipalityPathList):
    data = {}
    for file in municipalityPathList:
        try:
            with open(file, "r", encoding="utf-8") as municipalityFile:
                key = file.stem
                data[key] = json.load(municipalityFile)
        except Exception as e:
            print(f"Failed to read {file}: {e}")
    return data


def saveJsonContents(data, outputPath):
    try:
        with open(outputPath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"\nDebug file saved to: {outputPath}")
    except Exception as e:
        print(f"Failed to save debug file: {e}")

# TODO: Delete testing method
if __name__ == "__main__":
    # Step 1: Find JSON files
    jsonFilePaths = getMunicipalityProfiles()

    # Step 2: Read JSON contents
    jsonContent = readMunicipalityJson(jsonFilePaths)

    # Step 3: Save all contents to a single debug JSON
    saveJsonContents(jsonContent, "municipality_list.json")

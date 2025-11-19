import json
from pathlib import Path
from comparison_template import COMPARISON_TEMPLATE

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
        
def processSelections(selection1, selection2):
    municipalityPaths = getMunicipalityProfiles()
    
    # Convert user inputs into integers
    try:
        idx1 = int(selection1) - 1
        idx2 = int(selection2) - 1
    except ValueError:
        return "Selections must be numbers."

    # Bounds check
    if not (0 <= idx1 < len(municipalityPaths)) or not (0 <= idx2 < len(municipalityPaths)):
        return "Invalid selections. Please choose from the displayed list."
    
    # Get the actual Path objects
    firstPath = municipalityPaths[idx1]
    secondPath = municipalityPaths[idx2]

    # Now read JSON for each (must pass a list!)
    firstData = readMunicipalityJson([firstPath])
    secondData = readMunicipalityJson([secondPath])
    firstKey = next(iter(firstData))
    secondKey = next(iter(secondData))
    
    firstKey = next(iter(firstData))
    secondKey = next(iter(secondData))

    compareProfiles(firstData[firstKey], secondData[secondKey], firstKey, secondKey)

    return f"Compared {firstKey} and {secondKey}"

# Display of the profiles to compare
def compareProfiles(profileA, profileB, nameA, nameB):
    print("\n" + "="*80)
    print(f"{nameA:^40} | {nameB:^40}")
    print("="*80)

    for section, config in COMPARISON_TEMPLATE.items():
        print(f"\n--- {section} ---")

        # simple fields
        for field in config.get("fields", []):
            valA = getNested(profileA, field)
            valB = getNested(profileB, field)
            print(f"{field:35}: {str(valA)[:40]:40} | {str(valB)[:40]:40}")

        # nested field groups
        nested_cfg = config.get("nested", {})
        for label, key in nested_cfg.items():
            print(f"\n  {label}:")
            subA = profileA.get("Demographic", {}).get(key, {})
            subB = profileB.get("Demographic", {}).get(key, {})

            for sub_field in subA.keys():
                valA = subA.get(sub_field)
                valB = subB.get(sub_field)
                print(f"    {sub_field:30}: {str(valA):10} | {str(valB):10}")

    print("\n" + "="*80 + "\n")
    
# Safe nested lookup
def getNested(data, key):
    # handle top-level and nested keys
    if key in data:
        return data[key]

    for category in data.values():
        if isinstance(category, dict) and key in category:
            return category[key]

    return "N/A"

# TODO: Delete testing method
if __name__ == "__main__":
    # Step 1: Find JSON files
    jsonFilePaths = getMunicipalityProfiles()

    # Step 2: Read JSON contents
    jsonContent = readMunicipalityJson(jsonFilePaths)

    # Step 3: Save all contents to a single debug JSON
    saveJsonContents(jsonContent, "municipality_list.json")

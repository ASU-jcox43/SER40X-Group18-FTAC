import json
from pathlib import Path
from os.path import dirname, realpath
from comparison_template import COMPARISON_TEMPLATE

# Folder containing JSON files
# TODO Don't need profiles path anymore, replace with MongoDB
PROFILES_PATH = Path(dirname(realpath(__file__))) / "../municipality_profile/profiles"
PROFILES_PATH = PROFILES_PATH.resolve()

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
    
    print()

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
        
def processSelections(selection1, selection2):
    municipalityPaths = getMunicipalityProfiles()
    
    # Convert user inputs into integers
    try:
        idx1 = int(selection1) - 1
        idx2 = int(selection2) - 1
    except ValueError:
        return False

    # Bounds check
    if not (0 <= idx1 < len(municipalityPaths)) or not (0 <= idx2 < len(municipalityPaths)):
        return False
    
    # Get the actual Path objects
    firstPath = municipalityPaths[idx1]
    secondPath = municipalityPaths[idx2]

    # Now read JSON for each (must pass a list!)
    firstData = readMunicipalityJson([firstPath])
    secondData = readMunicipalityJson([secondPath])
    
    firstKey = next(iter(firstData))
    secondKey = next(iter(secondData))

    compareProfiles(firstData[firstKey], secondData[secondKey], firstKey, secondKey)

    return True

def getField(profile, section, field):
    # 1. Check top-level
    if field in profile:
        return profile[field]

    # 2. Check section dictionary (if exists)
    sec = profile.get(section)
    if isinstance(sec, dict):
        return sec.get(field, "N/A")

    return "N/A"


def compareProfiles(profileA, profileB, nameA, nameB):
    print("\n" + "="*100)
    print(f"{nameA:^50} | {nameB:^50}")
    print("="*100)

    for section, config in COMPARISON_TEMPLATE.items():
        print(f"\n--- {section} ---")

        for field in config.get("fields", []):
            valA = getField(profileA, section, field)
            valB = getField(profileB, section, field)
            print(f"{field:40}: {str(valA)[:45]:45} | {str(valB)[:45]:45}")

        for label, nestedKey in config.get("nested", {}).items():
            print(f"{label}:")

            secA = profileA.get(section, {})
            secB = profileB.get(section, {})

            subA = secA.get(nestedKey, {}) if isinstance(secA, dict) else {}
            subB = secB.get(nestedKey, {}) if isinstance(secB, dict) else {}

            # Handle list nested fields (like Adjacent Municipalities)
            if isinstance(subA, list) or isinstance(subB, list):
                listA = ", ".join(subA) if isinstance(subA, list) else "N/A"
                listB = ", ".join(subB) if isinstance(subB, list) else "N/A"
                print(f"    {listA:45} | {listB:45}")
                continue

            # Handle dict nested fields
            keys = sorted(set(subA.keys()) | set(subB.keys()))
            for k in keys:
                print(f"    {k:36}: {str(subA.get(k, 'N/A'))[:20]:45} | {str(subB.get(k, 'N/A'))[:20]}")

        if "list_fields" in config:
            listA = profileA.get(section, [])
            listB = profileB.get(section, [])

            max_len = max(len(listA), len(listB))

            print("Entries:")

            for i in range(max_len):
                entryA = listA[i] if i < len(listA) else {}
                entryB = listB[i] if i < len(listB) else {}

                print(f"    Entry {i+1}:")
                for lf in config["list_fields"]:
                    valA = entryA.get(lf, "N/A")
                    valB = entryB.get(lf, "N/A")
                    print(f"    {lf:36}: {str(valA)[:40]:45} | {str(valB)[:40]}")

    print("\n" + "="*100 + "\n")
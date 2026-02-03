from .comparison_template import COMPARISON_TEMPLATE
from Backend.Logic.mongo_db.profile_collection import getAllProfiles

# Folder containing JSON files

# Gets documents from 
def getMunicipalityProfiles():
    profiles = getAllProfiles()
    
    print(f"Found {len(profiles)} profiles\n")
    
    return profiles # Returns profiles from db as json
        
def processSelections(selection1, selection2):
    profiles = getMunicipalityProfiles()
    
    # Convert user inputs into integers
    try:
        idx1 = int(selection1) - 1
        idx2 = int(selection2) - 1
    except ValueError:
        return False

    # Bounds check
    if not (0 <= idx1 < len(profiles)) or not (0 <= idx2 < len(profiles)):
        return False
    
    # Get the actual Path objects
    firstProfile = profiles[idx1]
    secondProfile = profiles[idx2]

    nameA = firstProfile["Geographic"]["City"]
    nameB = secondProfile["Geographic"]["City"]

    compareProfiles(firstProfile, secondProfile, nameA, nameB)

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
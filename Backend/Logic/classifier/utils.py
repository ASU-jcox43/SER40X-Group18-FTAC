from collections import defaultdict
from Backend.Logic.mongo_db.classification_collection import getAllClassifications

CANADIAN_CITIES = [
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria", "Windsor"
]

def checkForConflicts():
    files = getAllClassifications()
    
    cityGroups = defaultdict(list)
    
    for file in files:
        city = extractCityFromFilename(file.get("filename"))
        print("City extracted: " + city)
        
        # Get 
        if city != "unkown":
            cityGroups[city].append(file)
            
    # Now compare only documents in the same city
    for city, documents in cityGroups.items():
        print(f"\nChecking conflicts for {city}")
        
        # Compare every document against every other document in same city
        for i in range(len(documents)):
            for j in range(i + 1, len(documents)):
                doc1 = documents[i]
                doc2 = documents[j]

                conflicts = check_for_conflicts(doc1, doc2)

                if conflicts:
                    print(f"\nConflict between:")
                    print(f" - {doc1['filename']}")
                    print(f" - {doc2['filename']}")
                    print(f"Conflicts found: {conflicts}")
        
def extractCityFromFilename(filename):
    filenameLower = filename.lower()
    for city in CANADIAN_CITIES:
        if city.lower() in filenameLower:
            return city
    
    return "unknown"
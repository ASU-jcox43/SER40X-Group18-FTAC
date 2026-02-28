from collections import defaultdict
from Backend.Logic.mongo_db.extraction_collection import getAllExtractions

CANADIAN_CITIES = [
    "Toronto", "Ottawa", "Vancouver", "Montreal", "Calgary",
    "Edmonton", "Winnipeg", "Quebec City", "Halifax", "Victoria", "Windsor"
]

def checkForConflicts():
    files = getAllExtractions()
    
    cityGroups = defaultdict(list)
    
    for file in files:
        city = extractCityFromFilename(file.get("file"))
        print("City extracted: " + city)
        
        # Get 
        if city != "unkown":
            cityGroups[city].append(file)
            
    # TODO: Finish checking for conflicts
    
    
        
def extractCityFromFilename(filename):
    filenameLower = filename.lower()
    for city in CANADIAN_CITIES:
        if city.lower() in filenameLower:
            return city
    
    return "unknown"

# TODO: Figure out a way to flag conflicts
def flagConflicts():
    pass

# TODO: Figure out a way to organize data extracted from text
def collectData():
    pass
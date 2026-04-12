from pprint import pprint

def createDemographic(
    population, avgAge, ethnicityComposition, houseSize, educationLevels
):
    # Create demographic information
    # Ethnicity composition includes percentage for each ethinicity in the municipality
    # Education levels include percentage of people with certain education levels
    return {
        "Average Age": avgAge,
        "Ethnicity Compisition": ethnicityComposition,
        "Population": population,
        "Average House Hold Size": houseSize,
        "Education Levels": educationLevels,
    }

def createGeographic(
    city, province, region, popSqMile, areaSqMiles, lat, long, adjMunicipalities
):
    # Create geographic information
    # The longitude and Latitude is the city center
    # Adjacent municipalities includes list of municipalities neighboring the profile
    return {
        "City": city,
        "Province": province,
        "Region": region,
        "Population Density Per Sq Mile": popSqMile,
        "Area Sq Miles": areaSqMiles,
        "Latitude": lat,
        "Longitude": long,
        "Adjacent Municipalities": adjMunicipalities,
    }

def createContactInfo(contacts):
    # Multiple contact information can be created
    # Contact information could include: Licensing, permit office,
    # parking/bylaw office, public health/food safety office, fire deparment office, etc

    return contacts

def createFriendlinessScore(score):
    # Create scoring system based on municipality profile and rubric
    # Foundational score (out of 10)
    # Licensing Requirements score (out of 10)
    # Operations & Restrictions score (out of 30)
    # Equity & Fairness PLACEHOLDER

    return score

def createScoreBreakdown(breakdown):
    # Detailed breakdown of scores for each section
    # Scoring rubric topics are proprietary information and cannot be shared

    # example response structure below
    return breakdown

    
def createEconomy(income, min_wage, comm_tax_rates):
    return {
        "Income Level": income,
        "Minimum Wage": min_wage,
        "Commercial Tax Rates": comm_tax_rates,
    }

def createMunicipalityProfile(
    name,
    title,
    file,
    fb_type,
    city,
    province,
    population,
    avgAge,
    ethnicityComposition,
    houseSize,
    educationLevel,  # list of education levels
    income,
    min_wage,
    comm_tax_rates,
    last_updated,
    region,
    popSqMile,
    areaSqMiles,
    lat,
    long,
    adjMunicipalities,  # list of neighboring municipalities
    friendlinessScore,
    friendlinessScoreBreakdown,
    contacts # list of contact info 
):

    profile = {
        "Name": name,
        "Title": title,
        "file": file,
        "fb_type": fb_type,
        "Demographic": createDemographic(
            population, avgAge, ethnicityComposition, houseSize, educationLevel
            ),
        "Economy": createEconomy(income, min_wage, comm_tax_rates),
        "Geographic": createGeographic(
            city, province, region, popSqMile, 
            areaSqMiles, lat, long, adjMunicipalities
            ),
        "friendlinessScore": createFriendlinessScore(friendlinessScore),
        "friendlinessScoreBreakdown": createScoreBreakdown(friendlinessScoreBreakdown),
        "Contact Information": createContactInfo(contacts),
        "last Updated": last_updated
    }

    return profile

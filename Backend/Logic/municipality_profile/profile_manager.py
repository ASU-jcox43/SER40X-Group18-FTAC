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


def createContactInfo(department, address, fax, phoneNumber, email, website, hours):
    # Multiple contact information can be created
    # Contact information could include: Licensing, permit office,
    # parking/bylaw office, public health/food safety office, fire deparment office, etc

    return {
        "Department": department,
        "Address": address,
        "Fax": fax,
        "Phone": phoneNumber,
        "Email": email,
        "Website": website,
        "Hours": hours,
    }


def createScore():
    # Create scoring system based on municipality profile and rubric
    # Foundational score (out of 10)
    # Licensing Requirements score (out of 10)
    # Operations & Restrictions score (out of 30)
    # Equity & Fairness PLACEHOLDER

    friendliness_index = scoreBreakdown()

    return {
        "Foundational Score": 0,
        "Licensing Requirements": 0,
        "Operations & Restrictions": 0,
        "Friendliness index": 0,
    }

def scoreBreakdown():
    # Detailed breakdown of scores for each section
    # Scoring rubric topics are proprietary information and cannot be shared

    # example response structure below
    friendlinessBreakdown = {
        "Foundational": {
            "Points Awarded": 0,
            "Points Available": 10,
            "Percentage": 0,
            "Friendliness Index": "Very friendly",
        },
        "Licensing Requirements": {
            "Points Awarded": 0,
            "Points Available": 10,
            "Percentage": 0,
            "Friendliness Index": "Very friendly",
        },
        "Operations & Restrictions": {
            "Points Awarded": 0,
            "Points Available": 30,
            "Percentage": 0,
            "Friendliness Index": "Very friendly",
        },
    }
    return friendlinessBreakdown

def createEconomy(income, min_wage, comm_tax_rates):
    return {
        "Income Level": income,
        "Minimum Wage": min_wage,
        "Commercial Tax Rates": comm_tax_rates,
    }

def createMunicipalityProfile(
    name,
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
    contacts # list of contact info 
):

    profile = {
        "Name": name,
        "fb_type": fb_type,
        "Province": province,
        "Demographic": createDemographic(
            population, avgAge, ethnicityComposition, houseSize, educationLevel
            ),
        "Economy": createEconomy(income, min_wage, comm_tax_rates),
        "Geographic": createGeographic(
            city, province, region, popSqMile, 
            areaSqMiles, lat, long, adjMunicipalities
            ),
        "Contact Information": contacts,
        "last Updated": last_updated
    }

    return profile

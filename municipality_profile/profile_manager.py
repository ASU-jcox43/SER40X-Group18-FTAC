def createDemographic(population, age, community):
    return {
        "Population": population,
        "Age": age,
        "community": community,
    }


def createGeographic(cityName, province, region, location, landArea, boundaries):
    # Example geographic profile section
    # City Name: City of Makrham
    # Province: Ontario
    # Region: York Region (Greater Toronto Area)
    # Location: East of Toronto
    # land Area: 212 sq km
    # Boundaries: {
    #        'North':'Whitechurch-Stouffville',
    #        'South': 'Toronto',
    #        'East': 'Pickering',
    #        'West': 'Vaughan'
    #   }

    return {
        "City Name": cityName,
        "Province": province,
        "Region": region,
        "Location": location,
        "Area": landArea,
        "Boundaries": boundaries,
    }


def createContactInfo(department, address, phone, email, website):
    # Multiple contact information can be created
    # Contact information could include: Licensing, permit office,
    # parking/bylaw office, public health/food safety office, fire deparment office, etc

    return {
        "Department": department,
        "Address": address,
        "Phone": phone,
        "Email": email,
        "Website": website,
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
        "Friendliness index": 0
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
            "Friendliness Index": "Very friendly"
        },
        "Licensing Requirements": {
            "Points Awarded": 0,
            "Points Available": 10,
            "Percentage": 0,
            "Friendliness Index": "Very friendly"
        },
        "Operations & Restrictions": {
            "Points Awarded": 0,
            "Points Available": 30,
            "Percentage": 0,
            "Friendliness Index": "Very friendly"
        }
    }
    return friendlinessBreakdown
    


# TODO: Add more aspects if needed
def createEconomy(income, minWage, commTaxRates):
    return {
        "Income Level": income,
        "Minimum Wage": minWage,
        "Commercial Tax Rates": commTaxRates,
    }


def createMunicipalityProfile(
    name, province, population, age, community, income, minWage, commTaxRates
):
    profile = {
        "Name": name,
        "Province": province,
        "Demographic": createDemographic(population, age, community),
        "Economy": createEconomy(income, minWage, commTaxRates),
        # "Geographic": createGeographic(),
        # "Contact Information": createContactInfo()
    }
    return profile


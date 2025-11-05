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


def createContactInfo(department, address, fax, phoneNumber, email, website):
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
    name, city, province, population, age, community, income, minWage, commTaxRates
):
    # --- Toronto Food Business Contacts ---

    contacts = [
        createContactInfo(
            department = "City of Toronto - License & Permit Issuing Office",
            address = "East York Civic Centre, 850 Coxwell Ave, Toronto, ON M4C 5R1",
            fax = "n/a",
            phoneNumber = "311 (within Toronto) or 416-392-2489 (outside Toronto)",
            email = "MLSBusinessLicense@toronto.ca",
            website="https://www.toronto.ca/services-payments/permits-licences-bylaws/food-trucks-food-carts-ice-cream-trucks/food-trucks/"
        ),
        createContactInfo(
            department= "Road Allowance Permit Office",
            address= "East York Civic Centre, 850 Coxwell Avenue, Toronto, ON M4C 5R1",
            fax = "n/a",
            phoneNumber= "311 (within Toronto) or 416-392-2489 (outside Toronto)",
            email= "MLSRoadAllowance@toronto.ca",
            website= "https://www.toronto.ca/services-payments/permits-licences-bylaws/road-allowance-permits/"
        ),
        createContactInfo(
            department="Toronto Public Health – Food Safety & Inspections",
            address="277 Victoria Street, Toronto, ON M5B 1W2",
            fax = "n/a",
            phoneNumber="416-338-7600",
            email="publichealth@toronto.ca",
            website="https://www.toronto.ca/community-people/health-wellness-care/health-programs-advice/food-safety/"
        ),

        createContactInfo(
            department="Green P Parking Permits (Food Truck Parking)",
            address="33 Queen Street East, Toronto, ON M5C 1R5",
            fax = "n/a",
            phoneNumber="416-393-7275",
            email="events@greenpmobility.com",
            website="https://www.greenp.com/"
        ),

        createContactInfo(
            department="Technical Standards & Safety Authority (TSSA)",
            address="345 Carlingview Drive, Toronto, ON M9W 6N9",
            fax = "n/a",
            phoneNumber="1-877-682-8772",
            email="customerservices@tssa.org",
            website="https://www.tssa.org/"
        )
    ]

    profile = {
        "Name": name,
        "City": city,
        "Province": province,
        "Demographic": createDemographic(population, age, community),
        "Economy": createEconomy(income, minWage, commTaxRates),
        # "Geographic": createGeographic(),
        "Contact Information": contacts
    }

    # Example: print all contacts
    for contact in contacts:
        print(contact)
    return profile


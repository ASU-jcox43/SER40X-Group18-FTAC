from pprint import pprint


# Most information can be accessed by data sources
def createDemographic(population, avgAge, ethnicity, houseSize, educationLevel):

    return {
        "Average Age": avgAge,
        "ethnicity": ethnicity,
        "Population": population,
        "Average House Hold Size": houseSize,
        "Education Level": educationLevel,
    }


def createGeographic(
    city, province, region, popSqMile, areaSqMiles, lat, long, adjMunicipalities
):

    return {
        "City": city,
        "Province": province,
        "Region": region,
        "Population Density Per Sq Mile": popSqMile,
        "Area": areaSqMiles,
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
    ethnicity,
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
):
    # --- Toronto Food Business Contacts ---

    contacts = [
        createContactInfo(
            department="City of Toronto License & Permit Issuing Office",
            address="East York Civic Centre, 850 Coxwell Ave, Toronto, ON M4C 5R1",
            fax="n/a",
            phoneNumber="311 (within Toronto) or 416-392-2489 (outside Toronto)",
            email="MLSBusinessLicense@toronto.ca",
            website="https://www.toronto.ca/services-payments/permits-licences-bylaws/food-trucks-food-carts-ice-cream-trucks/food-trucks/",
            hours="Monday to Friday, 8:30 AM to 4:30 PM (Closed 12:30 p.m. to 1:30 p.m. and on statutory holidays)",
        ),
        createContactInfo(
            department="Road Allowance Permit Office",
            address="East York Civic Centre, 850 Coxwell Avenue, Toronto, ON M4C 5R1",
            fax="n/a",
            phoneNumber="311 (within Toronto) or 416-392-2489 (outside Toronto)",
            email="MLSRoadAllowance@toronto.ca",
            website="https://www.toronto.ca/services-payments/permits-licences-bylaws/road-allowance-permits/",
            hours="Monday to Friday: 8:30 a.m. to 4:00 p.m.",
        ),
        createContactInfo(
            department="Toronto Public Health Food Safety & Inspections",
            address="277 Victoria Street, Toronto, ON M5B 1W2",
            fax="n/a",
            phoneNumber="416-338-7600",
            email="publichealth@toronto.ca",
            website="https://www.toronto.ca/community-people/health-wellness-care/health-programs-advice/food-safety/",
            hours="Monday to Friday: 8:30 a.m. to 4:30 p.m.",
        ),
        createContactInfo(
            department="Green P Parking Permits (Food Truck Parking)",
            address="33 Queen Street East, Toronto, ON M5C 1R5",
            fax="n/a",
            phoneNumber="416-393-7275",
            email="events@greenpmobility.com",
            website="https://www.greenp.com/",
            hours="Monday to Friday: 8:30 a.m. to  4:30 p.m.",
        ),
        createContactInfo(
            department="Technical Standards & Safety Authority (TSSA)",
            address="345 Carlingview Drive, Toronto, ON M9W 6N9",
            fax="n/a",
            phoneNumber="1-877-682-8772",
            email="customerservices@tssa.org",
            website="https://www.tssa.org/",
            hours="Monday to Friday: 8:00 a.m. to 5:00 p.m.",
        ),
    ]

    profile = {
        "Name": name,
        "fb_type": fb_type,
        "City": city,
        "Province": province,
        "Demographic": createDemographic(
            population, avgAge, ethnicity, houseSize, educationLevel
        ),
        "Economy": createEconomy(income, min_wage, comm_tax_rates),
        "Geographic": createGeographic(
            city, province, region, popSqMile, areaSqMiles, lat, long, adjMunicipalities
        ),
        "Contact Information": contacts,
        "last Updated": last_updated,
    }

    # Example: pprint all contacts
    for contact in contacts:
        pprint(contact)

    return profile

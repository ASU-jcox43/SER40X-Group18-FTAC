import json

def createDemographic(population, age, income, community):
    return {
        "Population": population,
        "Age": age,
        "income": income,
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
        "Boundaries": boundaries
    }

def createContactInfo(department, address, phone, email, website):
    # Multiple contact information can be created 
    return {
        "Department": department,
        "Address": address,
        "Phone": phone,
        "Email": email,
        "Website": website
    }

def createMunicipalityProfile(name, province, population, age, income, community):
    profile = {
        "Name": name,
        "Province": province,
        "Demographic": createDemographic(population, age, income, community),

    }
    return profile

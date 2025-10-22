import json


def createDemographic(population, age, income, community):
    return {
        "Population": population,
        "Age": age,
        "income": income,
        "community": community,
    }


def createProfile(name, province, population, age, income, community):
    profile = {
        "Name": name,
        "Province": province,
        "Demographic": createDemographic(population, age, income, community),
    }

    return profile

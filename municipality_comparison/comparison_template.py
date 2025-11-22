COMPARISON_TEMPLATE = {

    # Top-level simple values
    "Basic Info": {
        "fields": ["Name", "fb_type", "Province", "last Updated"]
    },

    # Demographics section with nested groups
    "Demographic": {
        "fields": ["Population", "Average Age", "Average House Hold Size"],
        "nested": {
            # Label                  # Key inside Demographic
            "Ethnicity Composition": "Ethnicity Compisition",
            "Education Levels": "Education Levels"
        }
    },

    # Economy section
    "Economy": {
        "fields": ["Income Level", "Minimum Wage", "Commercial Tax Rates"]
    },

    # Geography section
    "Geographic": {
        "fields": [
            "City",
            "Province",
            "Region",
            "Population Density Per Sq Mile",
            "Area Sq Miles",
            "Latitude",
            "Longitude"
        ],
        "nested": {
            # Adjacent municipalities is an array; treat it as a nested list
            "Adjacent Municipalities": "Adjacent Municipalities"
        }
    },

    # Special case: Contact Information is a list of objects
    # The comparison code will need to loop through each department
    "Contact Information": {
        "list_fields": [
            "Department",
            "Address",
            "Fax",
            "Phone",
            "Email",
            "Website",
            "Hours"
        ]
    }
}

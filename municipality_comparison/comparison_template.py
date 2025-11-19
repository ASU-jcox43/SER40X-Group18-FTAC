# TODO: Edit to include what data should be displayed

COMPARISON_TEMPLATE = {
    "Basic Info": {
        "fields": ["Name", "fb_type", "Province"]
    },

    "Demographics": {
        "fields": ["Population", "Average Age", "Average House Hold Size"],
        "nested": {
            "Ethnicity Composition": "Ethnicity Compisition"
        }
    },

    "Economy": {
        "fields": ["Income Level", "Minimum Wage", "Commercial Tax Rates"]
    },

    "Geographic": {
        "fields": ["City", "Region", "Population Density Per Sq Mile", "Area Sq Miles"]
    }
}

from openai import OpenAI
from docx import Document
import json
import os
from PyPDF2 import PdfReader

with open("config.json", "r") as f:
    config = json.load(f)

OPENAI_API_KEY = config["openai_api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)

INPUT_FOLDER = "../test documents/"
OUTPUT_FOLDER = "../reports/generated reports/"

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file using PyPDF2."""
    reader = PdfReader(pdf_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()

def extract_text(file_path: str) -> str:
    """Extract text from either a PDF or txt file."""
    if file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    elif file_path.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    else:
        return "" #this should never happen ideally

def generate_report_for_file(file_path: str, output_docx: str, prompt: str):
    """
    Reads a file, sends it with a prompt to the ChatGPT API,
    receives the output, and saves it as a .docx file.
    """
    text_input = extract_text(file_path)

    if not text_input.strip():
        print(f"Skipping unsupported/empty file: {file_path}")
        return

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that makes reports."},
            {"role": "user", "content": f"{prompt}\n\n---\n{text_input}"}
        ]
    )

    report_text = response.choices[0].message.content

    doc = Document()
    doc.add_paragraph(report_text)
    doc.save(output_docx)

    print(f"Report saved to: {output_docx}")

def process_folder(input_folder: str, output_folder: str, prompt: str):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".txt", ".pdf")):
            txt_path = os.path.join(input_folder, filename)

            name_only = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{name_only}_report.docx")

            generate_report_for_file(txt_path, output_path, prompt)

if __name__ == "__main__":
    prompt_text = """
    You are a report generator for a business that helps food truck business owners find information for their municipalities.
    Using a rubric, you are to make a score, and provide key information and recommendations for the report.
    You are to make the report with the following rubric:
    Does this local jurisdiction have a webpage, or section of a webpage, containing information specific to food trucks or mobile food?:
    2 points = Municipality hosts a dedicated webpage for Food Trucks
    1 point = Food Trucks are given their own section/sub-section on a municipal webpage with other aligned food business information
    0 points = Food Truck information only available via the bylaws or on a page that is unrelated to food businesses in general
    0 points = No centralized space given for Food Truck licensing information on municipal webpage
    0 points = N/A
    
    Does the local jurisdiction offer an easy-to-understand application checklist specifically for food trucks, located in the designated area for food truck information?:
    2 points = Checklist for application given
    1 point = Application form provided, included a checklist
    0 points = Application form provided, without a checklist
    0 points = Application form mentioned, but not accessible
    0 points = Application form not found
    
    Does this local jurisdiction offer an operational guide that provides clear and easy-to-understand instructions for new entrepreneurs on how to obtain a food truck license?:
    1 point = Operational guide available as a PDF document
    1 point = Municipal website hosts an operational guides page
    0 points = No operational guide given
    
    Does the local jurisdiction's website clearly display the bylaws that regulate the operation of food trucks, with direct links to the actual bylaws?:
    2 points = Applicable Bylaws are listed & linked on Food Truck webpage/section
    0 points = Applicable Bylaws are listed but not linked on Food Truck webpage/section
    1 point = Applicable Bylaws are available through linked pages in Food Truck webpage/section
    0 points = Applicable Bylaws are available on municipal website, but are not linked nor listed in Food Truck webpage/section
    0 points = Bylaws applicable to Food Trucks are not found
    
    Are the bylaws on the local jurisdiction’s website presented in a way that supports accessibility, including features like language translation and compatibility with screen readers?:
    1 point = Bylaws in accordance with accessibility web standards
    0 points = Bylaws not presented in accordance with accessibility web standards
    
    Does the local jurisdiction clearly state the penalties for violating food truck bylaws, including specific fines, operating restrictions, or license suspensions, so that operators fully understand the consequences of non-compliance?:
    2 points = Penalties specific to Food Trucks are detailed, with descriptions or fine values provided
    1 point = Generalized penalties applied to multiple businesses are detailed, with descriptions or fine values provided
    1 point = Penalties specific to Food Trucks are detailed, with no fine values provided
    1 point = Generalized penalties applied to multiple businesses are detailed, with no fine values provided
    0 points = Penalties mentioned without detailed description provided
    0 points = Unspecified
    
    Provincial business license (mandatory):
    2 points = Information and requirements for this license are provided with relevant links
    1 point = Mentions appear of this license, but information is limited
    0 points = No information is provided regarding this license
    
    Provincial food business license (uncommon):
    2 points = Information and requirements for this license are provided with relevant links
    1 point = Mentions appear of this license, but information is limited
    0 points = No information is provided regarding this license
    2 points = Not required
    
    "Municipal business license (currently assessing how common) 
    (NOTE: This is not a food truck license. There are some jurisdictions that require a general business license and a food truck OR food business license)":
    2 points = Information and requirements for this license are provided with relevant links
    1 point = Mentions appear of this license, but information is limited
    0 points = No information is provided regarding this license
    2 points = Not required
    
    Municipal food business/food truck license (common):
    2 points = Information and requirements for this license are provided with relevant links
    1 point = Mentions appear of this license, but information is limited
    0 points = No information is provided regarding this license
    0 points = Not required
    
    Retail license for CPG (Consumer Packaged Goods) (uncommon):
    2 points = Information and requirements for this license are provided with relevant links
    1 point = Mentions appear of this license, but information is limited
    0 points = No information is provided regarding this license
    2 points = Not required

    Are food trucks permitted to park on city streets to allow for curbside vending?:
    2 points = Yes, unrestricted
    1 point = Yes, with general language restrictions
    1 point = Yes, with clearly defined restrictions (ex, maps & boundaries)
    0 points = No, curbside vending is not allowed
    0 points = Unspecified
    
    What are the fees associated with occupying on-street parking spaces for food trucks in this jurisdiction?:
    2 points = All fees are waived
    1 point = Purchase a seasonal permit
    1 point = Pay a recurring fee (i.e. monthly) for on street parking
    0 points = Pay for metered parking while a spot is occupied
    0 points = Not permitted, NA
    0 points = Unspecified
    
    Are there any noise bylaws that restrict the operating hours of food trucks?:
    2 points = Operating hours are > the hours defined by noise ordinance bylaws
    1 point = Operating hours are = the hours defined by noise ordinance bylaws
    0 points = Operating hours are < the hours defined by noise ordinance bylaws
    0 points = Unspecified
    
    Are there any traffic bylaws that restrict the operating hours or locations of food trucks?:
    2 points = Operating hours are > the hours defined by traffic restriction bylaws
    1 point = Operating hours are = the hours defined by traffic restriction bylaws
    0 points = Operating hours are < the hours defined by traffic restriction bylaws
    0 points = Unspecified
    
    If there are restrictions on the number of hours food trucks are permitted to operate in this jurisdiction, what are those specific time restrictions?:
    2 points = > 5 hours
    1 point = > 3 hours, but <5 hours
    0 points = Less than 3 hours
    0 points = Unspecified
    
    Are there any regulations or restrictions that limit or prohibit the sale of branded consumer packaged goods from food trucks?:
    2 points = No Anti-CPG restrictions
    1 point = Food Trucks are required to get additional license or permit to sell CPGs
    0 points = Anti-CPG restricts Food Trucks from selling additional goods & merchandise
    0 points = Unspecified
    
    Does this local jurisdiction allow food trucks to operate on private property?:
    2 points = Yes, unrestricted
    1 point = Yes, with restrictions
    0 points = No, not permitted
    0 points = Unspecified
    
    Are there regulations limiting how close a food truck can operate to other food service businesses?:
    2 points = No limitations by proximity restrictions
    1 point = Limited by proximity requirements only in specific use cases
    0 points = Limited by proximity requirements
    0 points = Limited from operating in an entire geographic area
    
    Are there regulations that restrict food trucks from operating near certain non-food service businesses, such as schools, churches, or hospitals?:
    2 points = No limitations by proximity restrictions
    1 point = Limited by proximity requirements only in specific use cases
    0 points = Limited by proximity requirements
    0 points = Limited from operating in an entire geographic area
    0 points = Unspecified
    
    Does this local jurisdiction limit the number of food trucks allowed to operate within a specific geographic area?:
    2 points = No limitations on number of trucks in a given area
    1 point = Limitations are in line with traffic management, limited parking or noise bylaws
    0 points = The number of operators are limited in a given area
    0 points = Limited from operating in an entire geographic area
    0 points = The number of operators are limited in this jurisdiction
    0 points = Unspecified
    
    Does this jurisdiction explicitly define designated parking locations for food trucks, either through a location list or a map?:
    2 points = Not limited to designated parking spaces
    1 point = Limited to designated parking spaces provided on a map
    1 point = Limited to designated parking spaces defined via a written list of street locations
    0 points = Limited, but designated locations are not clearly defined
    0 points = Unspecified
    
    Beyond obtaining permission from the property owner, are there any additional restrictions in place for food trucks operating on private property in this jurisdiction?:
    0 points = Yes
    1 point = No
    0 points = Unspecified
    
    Does the local jurisdiction specify the name of the local authority responsible for conducting food safety inspections and enforcing regulations for food trucks?:
    2 points = Municipality names the local food & safety authority, providing links to that authorities food safety requirements
    1 point = Municipality names the local health authority, without providing link to the authority or its requirements
    0 points = Municipality does not outline the health authority responsible for food safety inspection
    
    Does the local jurisdiction provide a direct link to the website of the local authority responsible for food safety inspections and regulations for food trucks?:
    2 points = Municipality names the local food & safety authority, providing links to that authorities food safety requirements
    1 point = Municipality names the local health authority, without providing link to the authority or its requirements
    0 points = Municipality does not outline the health authority responsible for food safety inspection

    Does the local jurisdiction clearly specify the insurance requirements for food trucks, including minimum liability limits, provisions for additional insured parties, and any other relevant insurance information?:
    2 points = Municipality details insurance requirements, providing information regarding any requirements beyond minimum coverage
    1 point = Municipality provides some insurance requirements, including minimum coverage requirements
    0 points = Municipality states insurance is required, but provides no further details or information
    0 points = Unspecified
    
    "Does the local jurisdiction provide specific guidelines regarding the physical requirements that food trucks must meet, such as vehicle design or equipment, to ensure safe and sanitary operations? 
    NOTE: This question relates to the food preparation area - aka the INTERIOR of the truck. ":
    2 points = Requirements for Food Truck measurements or specifications outlined on municipal website
    1 point = Requirements for Food Truck measurements or specifications provided in municipal Bylaws
    0 points = Unspecified
    
    "Does the local jurisdiction provide clear guidelines regarding the exterior appearance of food trucks, including maintenance, decoration, signage, and any restrictions or permissions related to the surrounding area?
    NOTE: This question relates to the EXTERIOR of the truck":
    2 points = Exterior & perimeter requirements provided on municipal website, with detailed descriptions
    2 points = Exterior & perimeter requirements provided in municipal bylaws, with detailed descriptions
    1 point = Exterior & perimeter requirement mentioned on municipal website, with only vague or general descriptions (such as must be kept cleaned or in good condition without description of how those terms are appraised)
    0 points = Exterior & perimeter requirement mentioned in municipal bylaws, with only vague or general descriptions (such as must be kept cleaned or in good condition without description of how those terms are appraised)
    0 points = Unspecified
    """

    process_folder(INPUT_FOLDER, OUTPUT_FOLDER, prompt_text)
# Required Libraries
import cv2
import pytesseract
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import re
from datetime import datetime
from rapidfuzz import fuzz, process

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"c:\Program Files\Tesseract-OCR\tesseract.exe"

# Load the invoice image and extract text
def extract_image_to_text():
    image = Image.open("uploads/ornekler_ornek3.jpg")
    text = pytesseract.image_to_string(image).upper()
    return text

# Function to extract date from text
def extract_date(text):
    # Define possible date patterns
    date_patterns = [
        r'\b\d{2}/\d{2}/\d{4}\b',  # DD/MM/YYYY
        r'\b\d{2}-\d{2}-\d{4}\b',  # DD-MM-YYYY
        r'\b\d{4}/\d{2}/\d{2}\b',  # YYYY/MM/DD
        r'\b\d{4}-\d{2}-\d{2}\b'   # YYYY-MM-DD
    ]

    # Try to find a matching date pattern in the text
    for pattern in date_patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(0)  # Extracted date as a string

            # Try to parse the date to a datetime object
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"):
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    # Convert to DD/MM/YYYY format and return
                    return date_obj.strftime("%d/%m/%Y")
                except ValueError:
                    continue

    return "N/A"

# Function to extract time from text
def extract_time(text):
    time_patterns = [
        r'\b\d{2}:\d{2}:\d{2}\b',  # Matches HH:MM:SS
        r'\b\d{2}:\d{2}\b'         # Matches HH:MM
    ]
    
    # Loop through patterns to find a match
    for pattern in time_patterns:
        match = re.search(pattern, text)
        return match.group(0) if match else "N/A"

# Function to extract the tax office name from the text
def extract_tax_office_name(text):
    tax_office_keywords = [
        r'VD', r'VERGİ DAİRESİ', r'VERGİ D\.', r'V\.D\.', r'VERGİ DAİRESI', r'VERGİ DAIRESI'
    ]
    pattern = fr"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)\s+({'|'.join(tax_office_keywords)})"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        name = f"{match.group(1).strip()} {match.group(2).strip()}"
        return name
    return "N/A"

# Function to extract the tax office number from the text
def extract_tax_office_number(text):
    # Search for 'VD' or similar keywords followed by a valid 10-11 digit number
    pattern = r"(?:VD\.?|VERGİ DAİRESİ)\s*:?(\d{10,11})"

    # Perform regex search near 'VD'
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        return match.group(1)  # Extract and return the tax office number
    return "N/A"

# Function to extract product names from the text
def extract_product_names(text):
    product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
    return [name.strip() for name in product_names] if product_names else []

# Function to extract product costs from the text
def extract_product_costs(text):
    product_costs = re.findall(r"\*\s*([\d.,]+)", text)
    return [cost.strip() for cost in product_costs] if product_costs else []

# Function to extract VAT
def extract_vat(text):
    match = re.search(r"(\d{1,2}%|KDV\s*:\s*[\d.,]+)", text, re.IGNORECASE)
    return match.group(1) if match else "N/A"

def print_info(text):
    extracted_date = extract_date(text)
    extracted_time = extract_time(text)
    tax_office_name = extract_tax_office_name(text)
    tax_office_number = extract_tax_office_number(text)
    products = extract_product_names(text)
    costs = extract_product_costs(text)
    extracted_vat = extract_vat(text)
    print(extracted_date)
    print(extracted_time)
    print(tax_office_name)
    print(tax_office_number)
    print(products)
    print(costs)
    print(extracted_vat)

# Calling the functions and printing the results
text = extract_image_to_text()
print(text)
print_info(text)
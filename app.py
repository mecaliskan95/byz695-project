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
    image = Image.open("uploads/ornek_gorseller_ek10.png")
    raw_text = pytesseract.image_to_string(image).upper()  # Ensure Turkish language
    # Split the text into lines and remove any empty or whitespace-only lines
    cleaned_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    # Join the cleaned lines back into a single string
    cleaned_text = "\n".join(cleaned_lines)
    return cleaned_text

# Function to extract and validate the date from text
def extract_date(text):
    # Define a pattern to match dates with possible separators
    date_pattern = r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{4}[-/]\d{2}[-/]\d{2})\b"  # Handle MM/DD/YYYY and DD/MM/YYYY

    match = re.search(date_pattern, text)
    if match:
        date_str = match.group(1)  # Extract the matched date string
        possible_formats = ["%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d"]

        # Try each format to validate and reformat the date
        for fmt in possible_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                # Check if day and month are valid
                if 1 <= date_obj.day <= 31 and 1 <= date_obj.month <= 12:
                    return date_obj.strftime("%d/%m/%Y")  # Return in DD/MM/YYYY format
            except ValueError:
                continue  # Skip if the format doesn't match

    return "N/A"  # Return N/A if no valid date is found

# Function to extract and clean the time from text
def extract_time(text):
    # Define a pattern to match time with optional spaces or missing seconds
    time_pattern = r"\b(\d{2}):\s?(\d{2})(?::\s?(\d{2}))?\b"

    match = re.search(time_pattern, text)
    if match:
        # Extract hours, minutes, and optional seconds
        hour = match.group(1)
        minute = match.group(2)
        second = match.group(3) if match.group(3) else "00"  # Default to 00 if seconds are missing
        return f"{hour}:{minute}:{second}"  # Return the cleaned time

    return "N/A"  # Return N/A if no valid time is found

# Function to extract the tax office name from the text
def extract_tax_office_name(text):
    # Define keywords to search for tax office
    tax_office_keywords = [
        r'VD', r'VERGİ DAİRESİ', r'VERGİ D\.', r'V\.D\.', r'VERGİ DAİRESI', r'VERGİ DAIRESI'
    ]
    
    # Adjust regex to allow optional punctuation and spaces
    pattern = fr"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)[\.\s]*({'|'.join(tax_office_keywords)}):?"

    # Perform the regex search
    match = re.search(pattern, text, re.IGNORECASE)

    if match:
        # Return only the tax office name without the keyword (e.g., "GÖNEN")
        tax_office_name = match.group(1).strip()
        return tax_office_name

    return "N/A"  # Return 'N/A' if no match is found

# Function to extract the tax office number from the text
def extract_tax_office_number(text):
    # Split the text into lines to search for the line containing 'VD'
    lines = text.splitlines()

    for line in lines:
        # Check if 'VD' or 'VERGİ DAİRESİ' appears in the line
        if re.search(r"(VD\.?|VERGİ DAİRESİ)", line, re.IGNORECASE):
            # Now search for the 10-11 digit number in this specific line
            match = re.search(r"\b(\d{10,11})\b", line)
            if match:
                return match.group(1)  # Return the extracted number

    return "N/A"  # If no valid tax office number is found

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

# Print information
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
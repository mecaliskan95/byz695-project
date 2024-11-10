# Required Libraries
import os
import cv2
import re
import numpy as np
from flask import Flask, render_template, request, redirect
import pytesseract
from skimage.filters import threshold_local
import logging

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

# Create the Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Ensure the uploads directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

def bw_scanner(image):
    """Convert an image to black and white using local thresholding."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    T = threshold_local(gray, 21, offset=5, method="gaussian")
    return (gray > T).astype("uint8") * 255

class ImageProcessor:
    """Handles image processing and text extraction."""

    @staticmethod
    def preprocess_image(image_path):
        """Enhance the image and detect text boxes."""
        image = cv2.imread(image_path)

        # Apply black and white scanning
        bw_image = bw_scanner(image)

        # Find contours (text boxes)
        contours, _ = cv2.findContours(bw_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Draw bounding boxes around text
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30 and h > 10:  # Filter out small contours
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return image

    @staticmethod
    def extract_text(image_path):
        """Extract text from an image using Tesseract."""
        try:
            processed_image = ImageProcessor.preprocess_image(image_path)
            rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            text = pytesseract.image_to_string(rgb_image, lang='tur+eng').upper()
            logging.info(f"Extracted text: {text[:100]}...")  # Log the first 100 characters of the extracted text
            return text
        except Exception as e:
            logging.error(f"Error extracting text: {e}")
            return ""

class TextExtractor:
    """Handles text extraction from the OCR output."""

    @staticmethod
    def extract_date(text):
        """Extract date from text in various formats."""
        pattern = r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b"
        
        match = re.search(pattern, text)
        if match:
            day, month, year = match.groups()
            day, month, year = int(day), int(month), int(year)
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:  # Validate month, day, and year
                if month == 2:
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        if day > 29:
                            return "N/A"
                    else:
                        if day > 28:
                            return "N/A"
                elif month in [4, 6, 9, 11] and day > 30:
                    return "N/A"
                return f"{str(day).zfill(2)}/{str(month).zfill(2)}/{str(year)}"  # Ensures day and month are two digits
        
        return "N/A"  # Return "N/A" if no match is found or date is invalid

    @staticmethod
    def extract_time(text):
        """Extract time from text in HH:MM or HH:MM:SS format."""
        time_pattern = r"\b(\d{2}):(\d{2})(?::\d{2})?\b"  # Matches HH:MM:SS or HH:MM format

        match = re.search(time_pattern, text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:  # Validate hour and minute
                return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
        
        return "N/A"  # Return "N/A" if no match is found or time is invalid

    @staticmethod
    def extract_total_cost(text):
        """Extract total cost from text."""
        pattern = r"(?:TOPLAM|TUTAR)\s*[:\.]?\s*[\*\©\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_vat(text):
        """Extract VAT from text."""
        pattern = r"(?:TOPKDV|TOPLAM KDV|KDV(?:\s+\w+)?)\s*[:\.]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\s*\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.').replace(' ', '') if match else "N/A"

    @staticmethod
    def extract_tax_office_name(text):
        """Extract tax office name from text."""
        pattern = r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)\s*(?:(?:VD|V\.?D\.?|VERGİ DAİRESİ|VN)\s*[:\-]?)"

        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_name = match.group(1).strip()  # Capture and strip the matched name
            if matched_name:  # Check if the matched name is not empty
                return matched_name.split()[-1]  # Get only the last word
            else:
                return "N/A"  # If the matched name is empty, return "N/A"

        return "N/A"  # If no match is found, return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        """Extract tax office number from text."""
        lines = text.splitlines()
        keywords = [
            r"\bVD\b", r"\bVERGİ DAİRESİ\b", r"\bVN\b", r"\bVKN\b", r"\bTCKN\b", r"\bV\.D\."
        ]

        for line in lines:
            if any(re.search(keyword, line, re.IGNORECASE) for keyword in keywords):
                match = re.search(r"(?:(?:V\.?D\.?|VD|VERGİ DAİRESİ|VN|VKN|TCKN)\s*[:\-]?\s*)?(\d{10,11})", line)
                if match:
                    return match.group(1).strip()  # Return the extracted number
                
        return "N/A"

    @staticmethod
    def extract_product_names(text):
        """Extract product names from text."""
        product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
        return [name.strip() for name in product_names] if product_names else []

    @staticmethod
    def extract_product_costs(text):
        """Extract product costs from text."""
        product_costs = re.findall(r"\*\s*([\d.,]+)", text)
        return [cost.strip() for cost in product_costs] if product_costs else []

    @staticmethod
    def extract_invoice_number(text):
        """Extract invoice number from text."""
        patterns = [
            r"FİŞ NO[:\s]*([A-Za-z0-9\-]+)"
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "N/A"

@app.route("/", methods=["GET", "POST"])
def index():
    """Handle the main route for file upload and text extraction."""
    if request.method == "POST":
        if "file" not in request.files or not request.files["file"].filename:
            return redirect(request.url)

        file = request.files["file"]
        filename, file_extension = os.path.splitext(file.filename)

        if file_extension.lower() not in ['.jpg', '.jpeg', '.png', '.jfif']:
            return "Unsupported file type. Please upload a JPG, JPEG, PNG, or JFIF file."

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        try:
            text = ImageProcessor.extract_text(file_path)
            date = TextExtractor.extract_date(text)
            time = TextExtractor.extract_time(text)
            vat = TextExtractor.extract_vat(text)
            total_cost = TextExtractor.extract_total_cost(text)
            tax_office_name = TextExtractor.extract_tax_office_name(text)
            tax_office_number = TextExtractor.extract_tax_office_number(text)
            products = TextExtractor.extract_product_names(text)
            costs = TextExtractor.extract_product_costs(text)
            invoice_number = TextExtractor.extract_invoice_number(text)

            return render_template(
                "index.html",
                text=text,
                date=date,
                time=time,
                vat=vat,
                total_cost=total_cost,
                tax_office_name=tax_office_name,
                tax_office_number=tax_office_number,
                products=products,
                costs=costs,
                invoice_number=invoice_number
            )
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return "An error occurred while processing the file. Please try again."

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
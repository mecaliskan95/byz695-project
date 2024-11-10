# Required Libraries
import os
import cv2
import re
import numpy as np
from flask import Flask, render_template, request, redirect, jsonify
import pytesseract
from skimage.filters import threshold_local
import logging
from werkzeug.utils import secure_filename

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

# Create the Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

# Ensure the uploads directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'tiff'}

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
        bw_image = bw_scanner(image)
        contours, _ = cv2.findContours(bw_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30 and h > 10:
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return image

    @staticmethod
    def extract_text(image_path):
        """Extract text from an image using Tesseract."""
        try:
            processed_image = ImageProcessor.preprocess_image(image_path)
            rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            text = pytesseract.image_to_string(rgb_image, lang='tur+eng').upper()
            logging.info(f"Extracted text: {text[:100]}...")
            return text
        except Exception as e:
            logging.error(f"Error extracting text: {e}")
            return ""

class TextExtractor:
    """Handles text extraction from the OCR output."""

    @staticmethod
    def extract_date(text):
        """Extract date from the text."""
        pattern = r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b"
        match = re.search(pattern, text)
        if match:
            day, month, year = match.groups()
            day, month, year = int(day), int(month), int(year)
            if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                if month == 2:
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        if day > 29:
                            return "N/A"
                    else:
                        if day > 28:
                            return "N/A"
                elif month in [4, 6, 9, 11] and day > 30:
                    return "N/A"
                return f"{str(day).zfill(2)}/{str(month).zfill(2)}/{str(year)}"
        return "N/A"

    @staticmethod
    def extract_time(text):
        """Extract time from the text."""
        time_pattern = r"\b(\d{2}):(\d{2})(?::\d{2})?\b"
        match = re.search(time_pattern, text)
        if match:
            hour, minute = int(match.group(1)), int(match.group(2))
            if 0 <= hour < 24 and 0 <= minute < 60:
                return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
        return "N/A"

    @staticmethod
    def extract_total_cost(text):
        """Extract total cost from the text."""
        pattern = r"TOPLAM\s*[:\.]?\s*[\*\©\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_vat(text):
        """Extract VAT from the text."""
        pattern = r"(?:TOPKDV|TOPLAM KDV)\s*[:\.]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2}))"
        match = re.search(pattern, text)
        return match.group(1).replace(',', '.') if match else "N/A"

    @staticmethod
    def extract_tax_office_name(text):
        """Extract tax office name from the text."""
        keywords = [
            r'VD', r'VERGİ DAİRESİ', r'VERGİ D\.', r'V\.D\.', r'VERGİ DAİRESI', 
            r'VERGİ DAIRESI', r'VN'
        ]
        pattern = r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)\s*(?:(?:VD|V\.?D\.?|VERGİ DAİRESİ|VN)\s*[:\-]?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched_name = match.group(1).strip()
            if matched_name:
                return matched_name.split()[-1]
            else:
                return "N/A"
        return "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        """Extract tax office number from the text."""
        lines = text.splitlines()
        number_pattern = r"\b(\d{10,11})\b"
        keywords = [
            r"\bVD\b", r"\bVERGİ DAİRESİ\b", r"\bVN\b", r"\bVKN\b", r"\bTCKN\b", r"\bV\.D\."
        ]
        for line in lines:
            if any(re.search(keyword, line, re.IGNORECASE) for keyword in keywords):
                match = re.search(r"(?:(?:V\.?D\.?|VD|VERGİ DAİRESİ|VN|VKN|TCKN)\s*[:\-]?\s*)?(\d{10,11})", line)
                if match:
                    return match.group(1).strip()
        return "N/A"

    @staticmethod
    def extract_product_names(text):
        """Extract product names from the text."""
        product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
        return [name.strip() for name in product_names] if product_names else []

    @staticmethod
    def extract_product_costs(text):
        """Extract product costs from the text."""
        product_costs = re.findall(r"\*\s*([\d.,]+)", text)
        return [cost.strip() for cost in product_costs] if product_costs else []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            try:
                file.save(file_path)
                
                # Process the image and extract text
                extracted_text = ImageProcessor.extract_text(file_path)
                
                # Extract date, time, and total cost from the text
                extracted_date = TextExtractor.extract_date(extracted_text)
                extracted_time = TextExtractor.extract_time(extracted_text)
                extracted_total_cost = TextExtractor.extract_total_cost(extracted_text)
                extracted_vat = TextExtractor.extract_vat(extracted_text)
                extracted_tax_office_name = TextExtractor.extract_tax_office_name(extracted_text)
                extracted_tax_office_number = TextExtractor.extract_tax_office_number(extracted_text)
                extracted_product_names = TextExtractor.extract_product_names(extracted_text)
                extracted_product_costs = TextExtractor.extract_product_costs(extracted_text)
                
                return jsonify({
                    'date': extracted_date,
                    'time': extracted_time,
                    'total_cost': extracted_total_cost,
                    'vat': extracted_vat,
                    'tax_office_name': extracted_tax_office_name,
                    'tax_office_number': extracted_tax_office_number,
                    'product_names': extracted_product_names,
                    'product_costs': extracted_product_costs
                })
            except Exception as e:
                logger.error(f"Error processing file: {e}")
                return jsonify({'error': 'Error processing file'}), 500
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
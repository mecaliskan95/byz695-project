# Required Libraries
import os
import cv2
import re
import numpy as np
from flask import Flask, render_template, request, redirect
import pytesseract
from skimage.filters import threshold_local

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

# Create the Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Ensure the uploads directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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
        processed_image = ImageProcessor.preprocess_image(image_path)
        rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
        return pytesseract.image_to_string(rgb_image, lang='tur+eng').upper()


class TextExtractor:
    """Handles text extraction from the OCR output."""

    @staticmethod
    def extract_date(text):
        pattern = r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b"
        return re.search(pattern, text).group(1) if re.search(pattern, text) else "N/A"

    @staticmethod
    def extract_total_cost(text):
        pattern = r"TOPLAM[:\s]*([\d.,]+)"
        return re.search(pattern, text).group(1).replace(',', '.') if re.search(pattern, text) else "N/A"

    @staticmethod
    def extract_vat(text):
        pattern = r"TOP KDV[:\s]*([\d.,]+)"
        return re.search(pattern, text).group(1).replace(',', '.') if re.search(pattern, text) else "N/A"

    @staticmethod
    def extract_tax_office_name(text):
        keywords = [
            r'VD', r'VERGİ DAİRESİ', r'VERGİ D\.', r'V\.D\.', r'VERGİ DAİRESI', 
            r'VERGİ DAIRESI', r'VN'
        ]
        pattern = fr"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)[\.\s]*({'|'.join(keywords)})"
        return re.search(pattern, text, re.IGNORECASE).group(1).strip() if re.search(pattern, text) else "N/A"

    @staticmethod
    def extract_tax_office_number(text):
        lines = text.splitlines()
        number_pattern = r"\b(\d{10,11})\b"
        keywords = [
            r"\bVD\b", r"\bVERGİ DAİRESİ\b", r"\bVN\b", r"\bVKN\b", r"\bTCKN\b"
        ]
        for line in lines:
            if any(re.search(keyword, line, re.IGNORECASE) for keyword in keywords):
                match = re.search(number_pattern, line)
                if match:
                    return match.group(1)
        return "N/A"

    @staticmethod
    def extract_product_names(text):
        product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
        return [name.strip() for name in product_names] if product_names else []

    @staticmethod
    def extract_product_costs(text):
        product_costs = re.findall(r"\*\s*([\d.,]+)", text)
        return [cost.strip() for cost in product_costs] if product_costs else []


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files or not request.files["file"].filename:
            return redirect(request.url)

        file = request.files["file"]
        filename, file_extension = os.path.splitext(file.filename)

        # Allow jfif files
        if file_extension.lower() not in ['.jpg', '.jpeg', '.png', '.jfif']:
            return "Unsupported file type. Please upload a JPG, PNG, or JFIF file."

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        text = ImageProcessor.extract_text(file_path)
        date = TextExtractor.extract_date(text)
        vat = TextExtractor.extract_vat(text)
        total_cost = TextExtractor.extract_total_cost(text)
        tax_office_name = TextExtractor.extract_tax_office_name(text)
        tax_office_number = TextExtractor.extract_tax_office_number(text)
        products = TextExtractor.extract_product_names(text)
        costs = TextExtractor.extract_product_costs(text)

        return render_template(
            "index.html",
            text=text,
            date=date,
            vat=vat,
            total_cost=total_cost,
            tax_office_name=tax_office_name,
            tax_office_number=tax_office_number,
            products=products,
            costs=costs,
        )

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
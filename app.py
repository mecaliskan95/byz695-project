# Required Libraries
import os
import cv2
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
import pytesseract

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Create the Flask app
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"

# Ensure the uploads directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def preprocess_image(image_path):
    """Enhance the image for better OCR performance."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not load image from path: {image_path}")

    return image

def extract_image_to_text(image_path):
    """Extract text from an image using Tesseract."""
    processed_image = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_image, lang='tur+eng').upper()
    return text

def extract_date(text):
    date_pattern = r"\b(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})\b"
    match = re.search(date_pattern, text)
    if match:
        return match.group(1)
    return "N/A"

def extract_total_cost(text):
    total_cost_pattern = r"TOPLAM[:\s]*([\d.,]+)"
    match = re.search(total_cost_pattern, text)
    return match.group(1).replace(',', '.') if match else "N/A"

def extract_vat(text):
    vat_pattern = r"TOP KDV[:\s]*([\d.,]+)"
    match = re.search(vat_pattern, text)
    return match.group(1).replace(',', '.') if match else "N/A"

def extract_tax_office_name(text):
    tax_office_keywords = [
        r'VD', r'VERGİ DAİRESİ', r'VERGİ D\.', r'V\.D\.', r'VERGİ DAİRESI', 
        r'VERGİ DAIRESI', r'VN'
    ]
    pattern = fr"([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)[\.\s]*({'|'.join(tax_office_keywords)})"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"

def extract_tax_office_number(text):
    lines = text.splitlines()
    number_pattern = r"\b(\d{10,11})\b"
    tax_office_keywords = [
        r"\bVD\b", r"\bVERGİ DAİRESİ\b", r"\bVN\b", r"\bVKN\b", r"\bTCKN\b"
    ]
    for line in lines:
        if any(re.search(keyword, line, re.IGNORECASE) for keyword in tax_office_keywords):
            match = re.search(number_pattern, line)
            if match:
                return match.group(1)
    return "N/A"

def extract_product_names(text):
    product_names = re.findall(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*", text)
    return [name.strip() for name in product_names] if product_names else []

def extract_product_costs(text):
    product_costs = re.findall(r"\*\s*([\d.,]+)", text)
    return [cost.strip() for cost in product_costs] if product_costs else []

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            return redirect(request.url)

        if file:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(file_path)

            text = extract_image_to_text(file_path)
            date = extract_date(text)
            vat = extract_vat(text)
            total_cost = extract_total_cost(text)
            tax_office_name = extract_tax_office_name(text)
            tax_office_number = extract_tax_office_number(text)
            products = extract_product_names(text)
            costs = extract_product_costs(text)

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
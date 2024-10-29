import os
import cv2
import re
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from flask import Flask, render_template, request, redirect, flash, url_for
import pytesseract
from skimage.filters import threshold_local
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('receipt_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'

# Create Flask app with configurations
app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER="uploads",
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max file size
    SECRET_KEY=os.urandom(24),
    ALLOWED_EXTENSIONS={'jpg', 'jpeg', 'png', 'jfif'}
)

# Ensure uploads directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@dataclass
class ReceiptData:
    """Data class to store extracted receipt information."""
    date: str = "N/A"
    time: str = "N/A"
    vat: str = "N/A"
    total_cost: str = "N/A"
    tax_office_name: str = "N/A"
    tax_office_number: str = "N/A"
    products: List[str] = None
    costs: List[str] = None
    raw_text: str = ""

    def __post_init__(self):
        self.products = self.products or []
        self.costs = self.costs or []

class ImageEnhancer:
    """Handles image preprocessing and enhancement."""
    
    @staticmethod
    def apply_adaptive_threshold(image: np.ndarray) -> np.ndarray:
        """Apply adaptive thresholding to improve text contrast."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 5
        )

    @staticmethod
    def remove_noise(image: np.ndarray) -> np.ndarray:
        """Remove noise from the image using median blur."""
        return cv2.medianBlur(image, 3)

    @staticmethod
    def deskew(image: np.ndarray) -> np.ndarray:
        """Deskew the image if it's tilted."""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = 90 + angle
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

class TextProcessor:
    """Enhanced text processing with improved pattern matching."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text by removing extra spaces and standardizing characters."""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('İ', 'I').replace('ı', 'i')
        return text.upper().strip()

    @staticmethod
    def extract_date_time(text: str) -> Tuple[str, str]:
        """Extract date and time with improved pattern matching."""
        date_pattern = r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})"
        time_pattern = r"(\d{2}):(\d{2})(?::\d{2})?"
        
        date_match = re.search(date_pattern, text)
        time_match = re.search(time_pattern, text)
        
        date = "N/A"
        time = "N/A"
        
        if date_match:
            day, month, year = date_match.groups()
            try:
                # Validate date
                datetime(int(year), int(month), int(day))
                date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
            except ValueError:
                logger.warning(f"Invalid date found: {day}/{month}/{year}")
        
        if time_match:
            hour, minute = time_match.groups()
            if 0 <= int(hour) <= 23 and 0 <= int(minute) <= 59:
                time = f"{hour}:{minute}"
            
        return date, time

    @staticmethod
    def extract_monetary_value(text: str, pattern: str) -> str:
        """Extract and validate monetary values."""
        match = re.search(pattern, text)
        if match:
            value = match.group(1).replace(',', '.')
            try:
                float(value)  # Validate if it's a valid number
                return value
            except ValueError:
                logger.warning(f"Invalid monetary value found: {value}")
        return "N/A"

    @staticmethod
    def extract_products_and_costs(text: str) -> Tuple[List[str], List[str]]:
        """Extract product names and costs with improved accuracy."""
        lines = text.split('\n')
        products = []
        costs = []
        
        for line in lines:
            # Look for lines with product pattern: name followed by quantity and price
            match = re.match(r"([A-Za-zÇĞİÖŞÜçğıöşü\s]+)\s+\d+\s*\*\s*([\d.,]+)", line)
            if match:
                product_name = match.group(1).strip()
                cost = match.group(2).strip()
                if len(product_name) > 2:  # Filter out very short names
                    products.append(product_name)
                    costs.append(cost)
        
        return products, costs

class ReceiptProcessor:
    """Main class for processing receipts."""
    
    def __init__(self):
        self.image_enhancer = ImageEnhancer()
        self.text_processor = TextProcessor()

    def process_image(self, image_path: str) -> ReceiptData:
        """Process the receipt image and extract information."""
        try:
            # Read and enhance image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Failed to read image")

            # Apply image enhancements
            enhanced = self.image_enhancer.apply_adaptive_threshold(image)
            enhanced = self.image_enhancer.remove_noise(enhanced)
            enhanced = self.image_enhancer.deskew(enhanced)

            # Extract text
            text = pytesseract.image_to_string(enhanced, lang='tur+eng')
            normalized_text = self.text_processor.normalize_text(text)

            # Extract information
            date, time = self.text_processor.extract_date_time(normalized_text)
            products, costs = self.text_processor.extract_products_and_costs(normalized_text)

            return ReceiptData(
                date=date,
                time=time,
                vat=self.text_processor.extract_monetary_value(
                    normalized_text,
                    r"(?:TOPKDV|TOPLAM KDV)\s*[:\.]?\s*[\*\+\s]?[\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2}))"
                ),
                total_cost=self.text_processor.extract_monetary_value(
                    normalized_text,
                    r"TOPLAM\s*[:\.]?\s*[\*\©\#]?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{1,2}))"
                ),
                tax_office_name=self.extract_tax_office_name(normalized_text),
                tax_office_number=self.extract_tax_office_number(normalized_text),
                products=products,
                costs=costs,
                raw_text=text
            )
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}", exc_info=True)
            raise

    def extract_tax_office_name(self, text: str) -> str:
        """Extract tax office name with improved accuracy."""
        pattern = r"([A-ZÇĞİÖŞÜa-zçğıöşü\s\.]+?)\s*(?:(?:VD|V\.?D\.?|VERGİ DAİRESİ|VN)\s*[:\-]?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            return name.split()[-1] if name else "N/A"
        return "N/A"

    def extract_tax_office_number(self, text: str) -> str:
        """Extract tax office number with validation."""
        pattern = r"(?:(?:V\.?D\.?|VD|VERGİ DAİRESİ|VN|VKN|TCKN)\s*[:\-]?\s*)?(\d{10,11})"
        match = re.search(pattern, text)
        if match:
            number = match.group(1).strip()
            if len(number) in (10, 11):  # Validate number length
                return number
        return "N/A"

def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/", methods=["GET", "POST"])
def index():
    """Handle file upload and receipt processing."""
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file selected")
            return redirect(request.url)

        file = request.files["file"]
        if not file or not file.filename:
            flash("No file selected")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload a JPG, JPEG, PNG, or JFIF file.")
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            processor = ReceiptProcessor()
            receipt_data = processor.process_image(file_path)

            return render_template(
                "index.html",
                receipt_data=receipt_data,
                processed=True
            )

        except Exception as e:
            logger.error(f"Error processing receipt: {str(e)}", exc_info=True)
            flash("Error processing receipt. Please try again with a different image.")
            return redirect(request.url)

    return render_template("index.html", processed=False)

if __name__ == "__main__":
    app.run(debug=True)
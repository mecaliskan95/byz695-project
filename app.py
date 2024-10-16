# Required Libraries
from PIL import Image
import pytesseract
import re

# Configure Tesseract path (adjust as needed)
pytesseract.pytesseract.tesseract_cmd = r"c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Load the invoice image and extract text
image = Image.open("Capture2.PNG")
text = pytesseract.image_to_string(image)

# Debugging: print raw OCR output
print("OCR Output:\n", text)

# Extract multi-line tax office and tax number
tax_info = re.search(r"([A-Z\s]+)/\s*([A-Z\s]+)\s+([A-Z\s]+VD)\.\s*(\d+)", text, re.MULTILINE)

if tax_info:
    # Clean and format the tax office properly as "ISTANBUL, ESENLER VD"
    city = tax_info.group(2).strip()
    office = tax_info.group(3).strip()
    tax_office = f"{city}, {office}"
    tax_number = tax_info.group(4)
else:
    tax_office, tax_number = None, None

# Extract Date, Time, and Receipt Number
date = re.search(r"TARIH\s*:\s*(\d{2}/\d{2}/\d{4})", text)
time = re.search(r"SAAT\s*[:+]\s*(\d{2}:\d{2}:\d{2})", text)
receipt_no = re.search(r"FIS NO[;:]\s*(\d+)", text)

date = date.group(1) if date else None
time = time.group(1) if time else None
receipt_no = receipt_no.group(1) if receipt_no else None

# Extract Product Details (Name, VAT rate, Price)
product_pattern = r"(\D+)\s+%(\d+)\s*\*\s*([\d.,]+)"
products = re.findall(product_pattern, text)

product_details = [
    {"name": name.strip(), "vat_rate": f"{vat_rate}%", "price": float(price.replace(',', '.'))}
    for name, vat_rate, price in products
]

# Extract Total VAT and Total Amount (if available)
total_vat = re.search(r"Toplam KDV\s*:\s*([\d.,]+)", text)
total_amount = re.search(r"Toplam\s*:\s*([\d.,]+)", text)

total_vat = float(total_vat.group(1).replace(",", ".")) if total_vat else None
total_amount = float(total_amount.group(1).replace(",", ".")) if total_amount else None

# Structure the extracted data
invoice_data = {
    "tax_office": tax_office,
    "tax_number": tax_number,
    "date": date,
    "time": time,
    "receipt_no": receipt_no,
    "products": product_details,
    "total_vat": total_vat,
    "total_amount": total_amount
}

# Print the structured data using a loop
print("\nExtracted Invoice Data:")
for key, value in invoice_data.items():
    if key == "products":
        print("Products:")
        for product in value:
            print(f"- {product['name']} (VAT: {product['vat_rate']}, Price: {product['price']})")
    else:
        print(f"{key.replace('_', ' ').title()}: {value}")
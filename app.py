import sys
import os
import csv
from io import StringIO, BytesIO
from flask import Flask, render_template, request, send_file
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor
import tempfile

sys.dont_write_bytecode = True

app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

@app.route("/", methods=["POST"])
def process_files():
    texts = []
    filenames = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for file in request.files.getlist("files"):
            if file.filename:
                safe_filename = os.path.basename(file.filename)
                path = os.path.join(temp_dir, safe_filename)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                file.save(path)
                texts.append(ImageProcessor.extract_text(path))
                filenames.append(safe_filename)
    
    if texts:
        results = TextExtractor.extract_all(texts, filenames)
        return render_template("index.html", results=results, zip=zip)
    return render_template("index.html")

@app.route("/export-csv", methods=["POST"])
def export_csv():
    data = request.get_json()
    if not data:
        return "No data received", 400

    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    headers = [
        'Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number',
        'Total Cost', 'VAT', 'Payment Methods', 'Products'
    ]
    writer.writerow(headers)
    
    for row in data:
        products_str = "; ".join([
            f"{p.get('name', '')} ({p.get('cost', '')})" 
            for p in row.get('products', [])
        ])
        
        writer.writerow([
            str(row.get('filename', 'N/A')),
            str(row.get('date', 'N/A')),
            str(row.get('time', 'N/A')),
            str(row.get('tax_office_name', 'N/A')),
            str(row.get('tax_office_number', 'N/A')),
            str(row.get('total_cost', 'N/A')),
            str(row.get('vat', 'N/A')),
            str(row.get('payment_methods', 'N/A')),
            products_str
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode('utf-8-sig')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='invoice_data.csv'
    )

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
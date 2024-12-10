import sys
import os
import csv
from io import StringIO, BytesIO
from flask import Flask, render_template, request, send_file
import pytesseract
from config import Config
from text_extraction import TextExtractor
import tempfile
import shutil

app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

def save_uploaded_files():
    """Save uploaded files to temporary directory"""
    temp_dir = tempfile.mkdtemp()
    files_info = {'dir': temp_dir, 'paths': [], 'names': []}
    
    try:
        # Process each uploaded file
        for file in request.files.getlist("files"):
            if not file.filename:
                continue
                
            # Save file securely
            filename = os.path.basename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            
            # Store file information
            files_info['paths'].append(filepath)
            files_info['names'].append(filename)
            
        return files_info
        
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {'dir': None, 'paths': [], 'names': []}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method != "POST":
        return render_template("index.html")
        
    # Handle file upload
    files_info = save_uploaded_files()
    try:
        if files_info['paths']:
            results = TextExtractor.extract_all(files_info['paths'], files_info['names'])
            return render_template("index.html", results=results, zip=zip)
        return render_template("index.html")
    finally:
        if files_info['dir']:
            shutil.rmtree(files_info['dir'], ignore_errors=True)

@app.route("/export-csv", methods=["POST"])
def export_csv():
    if not (data := request.get_json()):
        return "No data received", 400

    # Prepare CSV writer
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Write headers
    headers = ['Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number',
              'Total Cost', 'VAT', 'Payment Methods']
    writer.writerow(headers)
    
    # Write data rows
    fields = ['filename', 'date', 'time', 'tax_office_name',
              'tax_office_number', 'total_cost', 'vat', 'payment_methods']
              
    for row in data:
        row_data = [str(row.get(field, 'N/A')) for field in fields]
        writer.writerow(row_data)
    
    # Prepare file for download
    output.seek(0)
    file_data = BytesIO(output.getvalue().encode('utf-8-sig'))
    
    return send_file(
        file_data,
        mimetype='text/csv',
        as_attachment=True,
        download_name='invoice_data.csv'
    )

if __name__ == "__main__":
    app.run(debug=True)
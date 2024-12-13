import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow logging
os.environ['KERAS_BACKEND'] = 'tensorflow'

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import csv
from io import StringIO, BytesIO
import asyncio
from concurrent.futures import ThreadPoolExecutor
import tempfile
import shutil
import logging
from flask import Flask, render_template, request, send_file
from text_extraction import TextExtractor

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tiff', 'bmp'}

logging.basicConfig(level=logging.WARNING)
app = Flask(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_files():
    temp_dir = tempfile.mkdtemp()
    files_info = {'dir': temp_dir, 'paths': [], 'names': []}
    try:
        for file in request.files.getlist("files"):
            if not file.filename:
                continue
            filename = os.path.basename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            files_info['paths'].append(filepath)
            files_info['names'].append(filename)
        logging.debug(f"Files saved: {files_info['names']}")
        return files_info
    except Exception as e:
        logging.error(f"Error saving files: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {'dir': None, 'paths': [], 'names': []}

async def process_files(files_info):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, TextExtractor.extract_all, files_info['paths'], files_info['names'])

@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method != "POST":
        return render_template("index.html")
    files_info = save_uploaded_files()
    try:
        if files_info['paths']:
            results = await process_files(files_info)
            return render_template("index.html", results=results, zip=zip)
        return render_template("index.html")
    finally:
        if files_info['dir']:
            shutil.rmtree(files_info['dir'], ignore_errors=True)

@app.route("/export-csv", methods=["POST"])
def export_csv():
    data = request.get_json()
    if not data:
        return "No data received", 400
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    headers = ['Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number', 'Total Cost', 'VAT', 'Payment Methods']
    writer.writerow(headers)
    fields = ['filename', 'date', 'time', 'tax_office_name', 'tax_office_number', 'total_cost', 'vat', 'payment_methods']
    for row in data:
        writer.writerow([str(row.get(field, 'N/A')) for field in fields])
    output.seek(0)
    file_data = BytesIO(output.getvalue().encode('utf-8-sig'))
    return send_file(file_data, mimetype='text/csv', as_attachment=True, download_name='invoice_data.csv')

if __name__ == "__main__":
    app.run(debug=True)
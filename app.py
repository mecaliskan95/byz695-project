import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['KERAS_BACKEND'] = 'tensorflow'

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import csv
from io import StringIO, BytesIO
import tempfile
import shutil
import logging
from flask import Flask, render_template, request, send_file
from text_extraction import TextExtractor
from werkzeug.utils import secure_filename
from ocr_methods import OCRMethods

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tiff', 'bmp'}

logging.basicConfig(level=logging.WARNING)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 120 * 1024 * 1024 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_files(files):
    temp_dir = tempfile.mkdtemp()
    try:
        files_info = {'paths': [], 'names': []}
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                files_info['paths'].append(filepath)
                files_info['names'].append(filename)
        
        if not files_info['paths']:
            return None
            
        return TextExtractor.extract_all(files_info['paths'], files_info['names'])
    except Exception as e:
        app.logger.error(f"Error processing files: {str(e)}")
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            files = request.files.getlist("files")
            if not files or all(file.filename == '' for file in files):
                return render_template("index.html", error="No files were uploaded")
                
            results = process_files(files)
            if not results:
                return render_template("index.html", error="No valid results were extracted")
                
            return render_template("index.html", results=results)
            
        except Exception as e:
            app.logger.error(f"Error processing files: {str(e)}")
            return render_template("index.html", error=f"Error processing files: {str(e)}")
    return render_template("index.html")

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
import os
from flask import Flask, render_template, request, redirect, flash
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor
import uuid

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.urandom(24)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

def trim_whitespace(text):
    return "\n".join(line.strip() for line in (text or "").splitlines() if line.strip())

app.jinja_env.filters['trim_whitespace'] = trim_whitespace

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method != "POST":
        return render_template("index.html")

    if "file" not in request.files or not request.files["file"].filename:
        flash("No file uploaded", "error")
        return redirect(request.url)

    file = request.files["file"]
    if not allowed_file(file.filename):
        flash("Invalid file type", "error")  
        return redirect(request.url)

    temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_filename)
    
    try:
        file.save(file_path)
        text = ImageProcessor.extract_text(file_path)
        
        if not text:
            raise ValueError("No text extracted from image")
            
        results = {
            'text': text,
            'date': TextExtractor.extract_date(text),
            'time': TextExtractor.extract_time(text),
            'vat': TextExtractor.extract_vat(text),
            'total_cost': TextExtractor.extract_total_cost(text),
            'tax_office_name': TextExtractor.extract_tax_office_name(text),
            'tax_office_number': TextExtractor.extract_tax_office_number(text),
            'products': TextExtractor.extract_product_names(text),
            'costs': TextExtractor.extract_product_costs(text),
            'invoice_number': TextExtractor.extract_invoice_number(text),
            'filename': file.filename
        }
        return render_template("index.html", **results, zip=zip)
    
    except Exception as e:
        flash(f"Error processing file: {str(e)}", "error")
        return redirect(request.url)
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    app.run(debug=True)
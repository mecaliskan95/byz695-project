import os
import logging
from flask import Flask, render_template, request, redirect, send_from_directory
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor

app = Flask(__name__)
app.config.from_object(Config)

def trim_whitespace(text):
    if not text:
        return ""
    text = text.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

app.jinja_env.filters['trim_whitespace'] = trim_whitespace
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD
logging.basicConfig(level=logging.INFO)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files or not request.files["file"].filename:
            logging.warning("No file part or filename in request")
            return redirect(request.url)

        file = request.files["file"]
        if not allowed_file(file.filename):
            logging.warning(f"Unsupported file type: {file.filename}")
            return "Unsupported file type. Please upload a JPG, JPEG, PNG, or JFIF file."

        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)

        try:
            text = ImageProcessor.extract_text(file_path)
            if not text:
                raise ValueError("No text extracted from image")
            date = TextExtractor.extract_date(text)
            time = TextExtractor.extract_time(text)
            vat = TextExtractor.extract_vat(text)
            total_cost = TextExtractor.extract_total_cost(text)
            tax_office_name = TextExtractor.extract_tax_office_name(text)
            tax_office_number = TextExtractor.extract_tax_office_number(text)
            products = TextExtractor.extract_product_names(text)
            costs = TextExtractor.extract_product_costs(text)
            invoice_number = TextExtractor.extract_invoice_number(text)

            return render_template(
                "index.html",
                text=text,
                date=date,
                time=time,
                vat=vat,
                total_cost=total_cost,
                tax_office_name=tax_office_name,
                tax_office_number=tax_office_number,
                products=products,
                costs=costs,
                invoice_number=invoice_number,
                zip=zip,
                filename=file.filename
            )
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return "An error occurred while processing the file. Please try again."

    return render_template("index.html")

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
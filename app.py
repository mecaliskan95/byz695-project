import os
import logging
from flask import Flask, render_template, request, redirect, send_from_directory  # Remove jsonify, make_response
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor
# Remove json and csv imports
# Remove StringIO import

app = Flask(__name__)
app.config.from_object(Config)

# Register the trim_whitespace filter before routes
def trim_whitespace(text):
    if not text:
        return ""
    # First trim the entire text
    text = text.strip()
    # Split into lines, remove empty lines, and trim each line
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    # Join with single newlines
    return "\n".join(lines)

app.jinja_env.filters['trim_whitespace'] = trim_whitespace

# Initialize Tesseract and logging
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
                zip=zip,  # Add zip function to template context
                filename=file.filename  # Add filename to template context
            )
        except Exception as e:
            logging.error(f"Error processing file: {e}")
            return "An error occurred while processing the file. Please try again."

    return render_template("index.html")

# Remove the entire @app.route("/export/<format>") function and its implementation

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)  # Use Config.UPLOAD_FOLDER

if __name__ == "__main__":
    app.run(debug=True)
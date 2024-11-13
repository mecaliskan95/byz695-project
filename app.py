import os
from flask import Flask, render_template, request, redirect, flash
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor
import uuid
import logging
from werkzeug.utils import secure_filename
import zipfile

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.urandom(24)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

logging.basicConfig(level=logging.DEBUG)

def trim_whitespace(text):
    return "\n".join(line.strip() for line in (text or "").splitlines() if line.strip())

app.jinja_env.filters['trim_whitespace'] = trim_whitespace

def allowed_file(filename):
    # Skip hidden files (starting with . or ._)
    if filename.startswith('.') or filename.startswith('._'):
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method != "POST":
        return render_template("index.html")

    if "files" not in request.files or not request.files.getlist("files"):
        flash("No files uploaded", "error")
        return redirect(request.url)

    files = request.files.getlist("files")
    logging.debug(f"Files received: {[file.filename for file in files]}")
    texts = []
    filenames = []

    for file in files:
        if not file.filename or not allowed_file(file.filename):
            logging.debug(f"Skipping file {file.filename} - not allowed or hidden")
            continue

        temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], temp_filename)
        
        try:
            file.save(file_path)
            logging.debug(f"File saved: {file_path}")

            if zipfile.is_zipfile(file_path):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(app.config["UPLOAD_FOLDER"])
                os.remove(file_path)
                for root, _, files in os.walk(app.config["UPLOAD_FOLDER"]):
                    for filename in files:
                        if allowed_file(filename):
                            file_path = os.path.join(root, filename)
                            try:
                                text = ImageProcessor.extract_text(file_path)
                                if text:
                                    texts.append(text)
                                    filenames.append(filename)
                            except Exception as e:
                                logging.warning(f"Failed to process file {filename}: {str(e)}")
                            finally:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
            else:
                try:
                    text = ImageProcessor.extract_text(file_path)
                    if text:
                        texts.append(text)
                        filenames.append(file.filename)
                except Exception as e:
                    logging.warning(f"Failed to process file {file.filename}: {str(e)}")
                finally:
                    if os.path.exists(file_path):
                        os.remove(file_path)

        except Exception as e:
            logging.error(f"Error processing file {file.filename}: {str(e)}")
            if os.path.exists(file_path):
                os.remove(file_path)
            continue

    if not texts:
        flash("No valid files were found or processed", "error")
        return redirect(request.url)

    results = TextExtractor.extract_all(texts)
    for result, filename in zip(results, filenames):
        result['filename'] = filename

    logging.debug(f"Extraction results: {results}")
    return render_template("index.html", results=results, zip=zip)

if __name__ == "__main__":
    app.run(debug=True)
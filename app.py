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
import base64
from contextlib import contextmanager
import tempfile
import shutil

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.urandom(24)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

logging.basicConfig(
    level=logging.ERROR,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def trim_whitespace(text: str) -> str:
    return "\n".join(line.strip() for line in (text or "").splitlines() if line.strip())

app.jinja_env.filters['trim_whitespace'] = trim_whitespace

def allowed_file(filename: str) -> bool:
    # Skip hidden files (starting with . or ._)
    if filename.startswith('.') or filename.startswith('._'):
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@contextmanager
def temporary_directory():
    temp_dir = tempfile.mkdtemp()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method != "POST":
        return render_template("index.html")

    with temporary_directory() as temp_dir:
        try:
            if "files" not in request.files or not request.files.getlist("files"):
                flash("No files uploaded", "error")
                return redirect(request.url)

            files = request.files.getlist("files")
            texts = []
            filenames = []

            for file in files:
                if not file.filename or not allowed_file(file.filename):
                    continue

                temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
                file_path = os.path.join(temp_dir, temp_filename)
                
                try:
                    file.save(file_path)
                    logging.debug(f"File saved: {file_path}")

                    if zipfile.is_zipfile(file_path):
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                        os.remove(file_path)
                        for root, _, files in os.walk(temp_dir):
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
                                # Use processed image instead of original
                                image_base64 = ImageProcessor.get_processed_image_base64(file_path)
                                filenames.append({"filename": file.filename, "image_base64": image_base64})
                        except Exception as e:
                            logging.error(f"Failed to process file {file.filename}: {str(e)}")
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
            for result, file_info in zip(results, filenames):
                result['filename'] = file_info["filename"]
                result['image_base64'] = file_info["image_base64"]

            logging.debug(f"Extraction results: {results}")
            return render_template("index.html", results=results, zip=zip)
        except Exception as e:
            logging.error(f"Error processing files: {str(e)}")
            flash("An error occurred while processing files", "error")
            return redirect(request.url)

if __name__ == "__main__":
    app.run(debug=True)
import sys
sys.dont_write_bytecode = True

import os
from flask import Flask, render_template, request
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor
import tempfile

app = Flask(__name__)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

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
        return render_template("index.html", results=results)
    return render_template("index.html")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
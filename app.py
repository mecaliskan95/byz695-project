import os
from flask import Flask, render_template, request, redirect
import pytesseract
from config import Config
from image_processing import ImageProcessor
from text_extraction import TextExtractor
import tempfile

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = os.urandom(24)
pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

@app.template_filter('trim_whitespace')
def trim_whitespace(text):
    if text:
        return "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return ""

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")

    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for file in request.files.getlist("files"):
            if not file.filename or not allowed_file(file.filename):
                continue

            temp_path = os.path.join(temp_dir, file.filename)
            file.save(temp_path)

            try:
                text = ImageProcessor.extract_text(temp_path)
                if text:
                    image_base64 = ImageProcessor.get_image_base64(temp_path)
                    extracted_data = TextExtractor.extract_all([text])[0]
                    extracted_data.update({
                        'filename': file.filename,
                        'image_base64': image_base64
                    })
                    results.append(extracted_data)
            except Exception as e:
                print(f"Error processing {file.filename}: {e}")

    return render_template("index.html", results=results, zip=zip)

if __name__ == "__main__":
    app.run(debug=True)
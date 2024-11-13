import os

class Config:
    UPLOAD_FOLDER = "static/uploads"
    TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe')
    # TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'c:\Program Files\Tesseract-OCR\tesseract.exe')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'jfif'}

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
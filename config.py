import os
import tempfile
from pathlib import Path

class Config:
    UPLOAD_FOLDER = Path(tempfile.gettempdir())
    TESSERACT_CMD = Path(os.getenv('TESSERACT_CMD', r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'))
    # TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'c:\Program Files\Tesseract-OCR\tesseract.exe')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'jfif'}
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
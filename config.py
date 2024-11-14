import os
from pathlib import Path

class Config:
    # TESSERACT_CMD = Path(os.getenv('TESSERACT_CMD', r'c:\Program Files\Tesseract-OCR\tesseract.exe'))
    TESSERACT_CMD = Path(os.getenv('TESSERACT_CMD', r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'))
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tfif'}

    @classmethod
    def validate_tesseract(cls):
        return cls.TESSERACT_CMD.exists()

if not Config.validate_tesseract():
    raise RuntimeError("Tesseract not found. Please install Tesseract or set correct path.")
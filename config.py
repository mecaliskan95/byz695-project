import os
from pathlib import Path

class Config:
    TESSERACT_CMD = Path(r'c:\Program Files\Tesseract-OCR\tesseract.exe')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    @classmethod
    def validate_tesseract(cls):
        return cls.TESSERACT_CMD.exists()

if not Config.validate_tesseract():
    raise RuntimeError("Tesseract not found. Please install Tesseract or set correct path.")
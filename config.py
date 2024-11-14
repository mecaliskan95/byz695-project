import os
import tempfile
from pathlib import Path
import shutil
from typing import Optional

class Config:
    UPLOAD_FOLDER = Path(tempfile.gettempdir())
    TESSERACT_CMD = Path(os.getenv('TESSERACT_CMD', r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'))
    # TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'c:\Program Files\Tesseract-OCR\tesseract.exe')
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'jfif'}
    
    @classmethod
    def validate_tesseract(cls) -> Optional[str]:
        if not cls.TESSERACT_CMD.exists():
            tesseract_path = shutil.which('tesseract')
            if tesseract_path:
                return Path(tesseract_path)
        return cls.TESSERACT_CMD if cls.TESSERACT_CMD.exists() else None

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Validate Tesseract installation
if not Config.validate_tesseract():
    raise RuntimeError("Tesseract not found. Please install Tesseract or set correct path.")
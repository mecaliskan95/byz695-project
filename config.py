import os
from pathlib import Path
import pytesseract

class Config:
    TESSERACT_PATHS = [
        r'c:\Program Files\Tesseract-OCR\tesseract.exe',
        r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        r'/opt/homebrew/Cellar/tesseract/5.4.1/bin/tesseract'
    ]
    
    TESSERACT_CMD = None
    for path in TESSERACT_PATHS:
        if os.path.exists(path):
            TESSERACT_CMD = Path(path)
            break

    if not TESSERACT_CMD:
        raise RuntimeError("Tesseract not found. Please install Tesseract or set correct path.")
    
    os.environ['TESSERACT_CMD'] = str(TESSERACT_CMD)
    pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_CMD)

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tfif', 'bmp'}
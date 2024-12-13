import os
import subprocess
import pytesseract
import easyocr
from paddleocr import PaddleOCR
from image_processing import ImageProcessor
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
import torch
import torchvision
from multiprocessing import Pool
import logging
from pathlib import Path
import ssl

logging.getLogger('ppocr').setLevel(logging.WARNING)
logging.getLogger('easyocr').setLevel(logging.WARNING)
logging.getLogger('paddleocr').setLevel(logging.WARNING)

class OCRMethods:
    _easyocr_reader = None
    _paddleocr_reader = None
    _tesseract_initialized = False

    TESSERACT_PATHS = [
        r'c:\Program Files\Tesseract-OCR\tesseract.exe',
        r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        r'/opt/homebrew/Cellar/tesseract/5.4.1/bin/tesseract'
    ]

    @classmethod
    def get_easyocr_reader(cls):
        if cls._easyocr_reader is None:
            try:
                cls._easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=True)
            except Exception as e:
                logging.warning(f"GPU not available for EasyOCR, defaulting to CPU: {e}")
                cls._easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=False)
        return cls._easyocr_reader

    @classmethod
    def get_paddleocr_reader(cls):
        if cls._paddleocr_reader is None:
            cls._paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='en')
        return cls._paddleocr_reader

    @classmethod
    def initialize_tesseract(cls):
        if not cls._tesseract_initialized:
            for path in cls.TESSERACT_PATHS:
                if os.path.exists(path):
                    os.environ['TESSERACT_CMD'] = str(Path(path))
                    pytesseract.pytesseract.tesseract_cmd = str(Path(path))
                    cls._tesseract_initialized = True
                    break
            if not cls._tesseract_initialized:
                raise RuntimeError("Tesseract not found. Please install Tesseract or set correct path.")

    @staticmethod
    def extract_with_pytesseract(image_path):
        OCRMethods.initialize_tesseract()
        if not os.path.isfile(image_path):
            return None
        processed_image = ImageProcessor.process_image(image_path)
        if processed_image is None:
            return None
        
        return pytesseract.image_to_string(
            processed_image, 
            lang='tur+eng',
        ).upper()

    @staticmethod
    def extract_with_easyocr(image_path):
        if not os.path.isfile(image_path):
            return None
        try:
            processed_image = ImageProcessor.process_image(image_path)
            if processed_image is None:
                return None
            result = OCRMethods.get_easyocr_reader().readtext(processed_image)
            return "\n".join([line[1] for line in result]).upper() if result else None
        except Exception as e:
            print(f"Error during easyocr processing: {e}")
            return None

    @staticmethod
    def extract_with_paddleocr(image_path):
        if not os.path.isfile(image_path):
            return None
        try:
            result = OCRMethods.get_paddleocr_reader().ocr(image_path, cls=True)
            return "\n".join([line[1][0] for line in result[0]]).upper() if result else None
        except Exception as e:
            print(f"Error during PaddleOCR processing: {e}")
            return None

    @staticmethod
    def extract_with_suryaocr(image_path):
        if not os.path.isfile(image_path):
            print(f"File not found: {image_path}")
            return None
        try:
            image = Image.open(image_path)
            langs = ["tr", "en"]
            det_processor, det_model = load_det_processor(), load_det_model()
            rec_model, rec_processor = load_rec_model(), load_rec_processor()

            predictions = run_ocr([image], [langs], det_model, det_processor, rec_model, rec_processor)
            text_lines = []
            for page in predictions:
                for line in page.text_lines:
                    text_lines.append(line.text)
            text = "\n".join(text_lines)
            return text.upper()
        except Exception as e:
            print(f"Error during Surya OCR processing: {e}")
            return None

    @staticmethod
    def extract_with_llamaocr(image_path):
        if not os.path.isfile(image_path):
            return None
        try:
            result = subprocess.run(['node', 'app.js', image_path], capture_output=True, text=True, check=True, encoding='utf-8')
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.CalledProcessError as e:
            print(f"Error during llama-ocr processing: {e.stderr.strip()}")
            return None
        except Exception as e:
            print(f"Unexpected error during llama-ocr processing: {e}")
            return None

    @staticmethod
    def batch_process_ocr(image_paths, ocr_method):
        with Pool() as pool:
            return pool.map(ocr_method, image_paths)

# Initialize OCR engines when module is imported
# OCRMethods.initialize()
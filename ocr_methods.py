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

logging.getLogger('ppocr').setLevel(logging.WARNING)
logging.getLogger('easyocr').setLevel(logging.WARNING)
logging.getLogger('paddleocr').setLevel(logging.WARNING)

class OCRMethods:
    try:
        easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=True)
    except Exception as e:
        logging.warning(f"GPU not available for EasyOCR, defaulting to CPU: {e}")
        easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=False)
    paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='en')

    @staticmethod
    def load_dictionary():
        encodings = ['utf-8', 'iso-8859-9', 'cp1254', 'latin1']  # Turkish encodings
        for encoding in encodings:
            try:
                with open('words.dic', 'r', encoding=encoding) as f:
                    return {word.strip().upper() for word in f.readlines()}
            except UnicodeDecodeError:
                continue
            except FileNotFoundError:
                print("Dictionary file not found.")
                return set()
        print(f"Could not read dictionary file with any of the encodings: {encodings}")
        return set()

    @staticmethod
    def extract_with_pytesseract(image_path):
        if not os.path.isfile(image_path):
            return None
        processed_image = ImageProcessor.process_image(image_path)
        if processed_image is None:
            return None
        return pytesseract.image_to_string(processed_image, lang='tur+eng', config='--oem 3 --psm 6').upper()

    @staticmethod
    def extract_with_easyocr(image_path):
        if not os.path.isfile(image_path):
            return None
        try:
            processed_image = ImageProcessor.process_image(image_path)
            if processed_image is None:
                return None
            result = OCRMethods.easyocr_reader.readtext(processed_image)
            return "\n".join([line[1] for line in result]).upper() if result else None
        except Exception as e:
            print(f"Error during easyocr processing: {e}")
            return None

    @staticmethod
    def extract_with_paddleocr(image_path):
        if not os.path.isfile(image_path):
            return None
        try:
            result = OCRMethods.paddleocr_reader.ocr(image_path, cls=True)
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
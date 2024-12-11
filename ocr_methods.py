import os
import subprocess
import pytesseract
import easyocr
import torch
from paddleocr import PaddleOCR
from image_processing import ImageProcessor
import json
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
import torch
import torchvision
from multiprocessing import Pool
import hashlib
import logging

# Suppress TensorFlow INFO and WARNING messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

class OCRMethods:
    use_gpu = torch.cuda.is_available()
    easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=use_gpu)
    paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=use_gpu)
    cache = {}

    @staticmethod
    def load_dictionary():
        try:
            with open('words.dic', 'r', encoding='utf-8', errors='ignore') as f:
                return {word.strip().upper() for word in f.readlines()}
        except FileNotFoundError:
            print("Dictionary file not found.")
            return set()

    @staticmethod
    def get_cache_key(image_path):
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    @staticmethod
    def extract_with_pytesseract(image_path):
        cache_key = OCRMethods.get_cache_key(image_path)
        if cache_key in OCRMethods.cache:
            return OCRMethods.cache[cache_key]
        
        if not os.path.isfile(image_path):
            return None
        processed_image = ImageProcessor.process_image(image_path)
        if processed_image is None:
            return None
        text = pytesseract.image_to_string(
            processed_image,
            lang='tur+eng',
            config='--oem 3 --psm 6'
        ).upper()
        OCRMethods.cache[cache_key] = text
        return text

    @staticmethod
    def extract_with_easyocr(image_path):
        cache_key = OCRMethods.get_cache_key(image_path)
        if cache_key in OCRMethods.cache:
            return OCRMethods.cache[cache_key]
        
        if not os.path.isfile(image_path):
            print(f"File not found: {image_path}")
            return None
        try:
            processed_image = ImageProcessor.process_image(image_path)
            if processed_image is None:
                return None
            result = OCRMethods.easyocr_reader.readtext(processed_image)
            if not result:
                print(f"No text found in image: {image_path}")
            text = "\n".join([line[1] for line in result]).upper() if result else None
            OCRMethods.cache[cache_key] = text
            return text
        except Exception as e:
            print(f"Error during easyocr processing: {e}")
            return None

    # @staticmethod
    # def extract_with_llamaocr(image_path):
    #     cache_key = OCRMethods.get_cache_key(image_path)
    #     if cache_key in OCRMethods.cache:
    #         return OCRMethods.cache[cache_key]
        
    #     if not os.path.isfile(image_path):
    #         print(f"File not found: {image_path}")
    #         return None
    #     try:
    #         result = subprocess.run(
    #             ['node', 'app.js', image_path],
    #             capture_output=True,
    #             text=True,
    #             check=True
    #         )
    #         if result.returncode != 0:
    #             print(f"Llama OCR error: {result.stderr.strip()}")
    #             return None
    #         text = result.stdout.strip().replace('**', '\n**')
    #         OCRMethods.cache[cache_key] = text
    #         return text
    #     except subprocess.CalledProcessError as e:
    #         print(f"Error during llama-ocr processing: {e}")
    #         return None

    @staticmethod
    def extract_with_paddleocr(image_path):
        cache_key = OCRMethods.get_cache_key(image_path)
        if cache_key in OCRMethods.cache:
            return OCRMethods.cache[cache_key]
        
        if not os.path.isfile(image_path):
            print(f"File not found: {image_path}")
            return None
        try:
            result = OCRMethods.paddleocr_reader.ocr(image_path, cls=True)
            if not result:
                print(f"No text found in image: {image_path}")
            text = "\n".join([line[1][0] for line in result[0]]).upper() if result else None
            OCRMethods.cache[cache_key] = text
            return text
        except Exception as e:
            print(f"Error during PaddleOCR processing: {e}")
            return None

    @staticmethod
    def extract_with_suryaocr(image_path):
        cache_key = OCRMethods.get_cache_key(image_path)
        if cache_key in OCRMethods.cache:
            return OCRMethods.cache[cache_key]
        
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
            OCRMethods.cache[cache_key] = text
            return text.upper()
        except Exception as e:
            print(f"Error during Surya OCR processing: {e}")
            return None

    @staticmethod
    def batch_process_ocr(image_paths, ocr_method):
        with Pool() as pool:
            results = pool.map(ocr_method, image_paths)
        return results
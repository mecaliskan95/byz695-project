import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import subprocess
import pytesseract
import easyocr
from PIL import Image
import logging
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
from multiprocessing import Pool
from image_processing import ImageProcessor
from paddleocr import PaddleOCR
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from functools import lru_cache

logging.getLogger('easyocr').setLevel(logging.WARNING)

class OCRMethods:
    _instances = {}
    _cache = {}
    _tesseract_initialized = False
    
    TESSERACT_PATHS = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\mecal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        r'/usr/bin/tesseract',
        r'/usr/local/bin/tesseract',
    ]

    @classmethod
    def initialize_tesseract(cls):
        if cls._tesseract_initialized:
            return True
            
        for path in cls.TESSERACT_PATHS:
            if os.path.exists(path):
                try:
                    pytesseract.pytesseract.tesseract_cmd = str(Path(path))
                    pytesseract.get_languages()
                    cls._tesseract_initialized = True
                    print(f"Tesseract initialized successfully at: {path}")
                    return True
                except Exception as e:
                    print(f"Failed to initialize Tesseract at {path}: {e}")
                    continue
        
        print("ERROR: Tesseract is not properly installed or configured.")
        print("Please install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("Make sure to install the Turkish language data as well.")
        return False

    @classmethod
    @lru_cache(maxsize=1)
    def get_instance(cls, method_name):
        if method_name not in cls._instances:
            if method_name == 'easyocr':
                cls._instances[method_name] = easyocr.Reader(['en', 'tr'], gpu=False)
            elif method_name == 'paddle':
                cls._instances[method_name] = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            elif method_name == 'tesseract':
                cls.initialize_tesseract()
        return cls._instances.get(method_name)

    @classmethod
    def process_with_method(cls, image_path, method_name, processor_func):
        cache_key = f"{image_path}_{method_name}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        if not os.path.isfile(image_path):
            print(f"File not found: {image_path}")
            return None

        try:
            processed_image = cls.process_image_cached(image_path)
            if processed_image is None:
                print(f"Image processing failed for {image_path}")
                return None

            result = processor_func(processed_image)
            if result and len(result.strip()) > 0:
                cls._cache[cache_key] = result.upper()
                return cls._cache[cache_key]
            else:
                print(f"{method_name} produced empty result for {image_path}")
                return None
                
        except Exception as e:
            print(f"Error in {method_name} for {image_path}: {str(e)}")
            return None

    @staticmethod
    @lru_cache(maxsize=32)
    def process_image_cached(image_path):
        return ImageProcessor.process_image(image_path)

    @classmethod
    def extract_with_pytesseract(cls, image_path):
        if not cls.initialize_tesseract():
            print("Falling back to other OCR methods...")
            return None
            
        return cls.process_with_method(
            image_path,
            'tesseract',
            lambda img: pytesseract.image_to_string(img, lang='tur+eng')
        )

    @classmethod
    def extract_with_easyocr(cls, image_path):
        def process(img):
            reader = cls.get_instance('easyocr')
            results = reader.readtext(img)
            if not results:
                return None
                
            lines = []
            current_line = []
            line_threshold = 20

            for result in results:
                box, text, confidence = result
                
                if confidence < 0.1:
                    continue
                    
                if not current_line:
                    current_line.append(result)
                else:
                    if abs(box[0][1] - current_line[0][0][0][1]) < line_threshold:
                        current_line.append(result)
                    else:
                        current_line.sort(key=lambda x: x[0][0][0])  # Sort by x-coordinate
                        line_text = " ".join(res[1].strip() for res in current_line)
                        lines.append(line_text)
                        current_line = [result]

            if current_line:
                current_line.sort(key=lambda x: x[0][0][0])
                line_text = " ".join(res[1].strip() for res in current_line)
                lines.append(line_text)

            return "\n".join(lines)

        return cls.process_with_method(image_path, 'easyocr', process)

    @classmethod
    def extract_with_llamaocr(cls, image_path):
        if not os.path.isfile(image_path):
            return None
            
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            node_script = os.path.join(current_dir, 'app.js')
            
            result = subprocess.run(
                ['node', node_script, image_path], 
                capture_output=True, 
                text=True, 
                check=True, 
                encoding='utf-8',
                cwd=current_dir
            )
            
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip().upper()
            
            return None
            
        except subprocess.CalledProcessError as e:
            print(f"Error during llama-ocr processing: {e.stderr.strip()}")
            return None
        except Exception as e:
            print(f"Unexpected error during llama-ocr processing: {e}")
            return None

    @staticmethod
    def extract_with_paddleocr(image_path):
        if not os.path.isfile(image_path):
            return None
        try:
            processed_image = OCRMethods.process_image_cached(image_path)
            if processed_image is None:
                return None

            ocr = OCRMethods.get_instance('paddle')
            if ocr is None:
                return None

            result = ocr.ocr(processed_image)
            if not result or not result[0]:
                return None

            lines = []
            current_line = []
            current_y = None
            threshold = 20

            for line in result[0]:
                box, (text, confidence) = line
                if confidence < 0.5:
                    continue

                y1 = (box[0][1] + box[3][1]) / 2

                if current_y is None or abs(current_y - y1) < threshold:
                    current_line.append(text)
                    current_y = y1
                else:
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [text]
                    current_y = y1

            if current_line:
                lines.append(" ".join(current_line))

            return "\n".join(lines).upper()

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
    def batch_process_ocr(image_paths, ocr_method, batch_size=4):
        results = []
        for i in range(0, len(image_paths), batch_size):
            batch = image_paths[i:i + batch_size]
            with Pool(min(len(batch), os.cpu_count() or 1)) as pool:
                results.extend(pool.map(ocr_method, batch))
        return results
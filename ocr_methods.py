import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

import subprocess
import pytesseract
import easyocr
from PIL import Image
from pathlib import Path
from paddleocr import PaddleOCR
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor
from image_processing import ImageProcessor

# Add these imports at the top with the other imports
import warnings
import logging

# Add after imports
warnings.filterwarnings('ignore')  # This will disable the GPU warning
logging.getLogger('easyocr').setLevel(logging.ERROR)  # This will disable EasyOCR's warnings

TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Users\mecal\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
    r'c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
    r'/usr/bin/tesseract',
    r'/usr/local/bin/tesseract',
]

for path in TESSERACT_PATHS:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = str(Path(path))
        pytesseract.get_tesseract_version()

_easyocr_reader = None
_paddle_ocr = None

class OCRMethods:
    @staticmethod
    def _calculate_adaptive_threshold(image):
        """Calculate adaptive threshold based on image height"""
        try:
            height = None
            
            if isinstance(image, (int, float)): 
                height = int(image)
            elif isinstance(image, Image.Image):
                height = image.size[1]
            elif hasattr(image, 'shape'):
                height = image.shape[0]
            elif isinstance(image, (list, tuple)):
                height = image[1] if len(image) > 1 else 1000

            base_threshold = 10
            min_threshold = 10
            max_threshold = 30
            
            adaptive_threshold = int((height / 1000.0) * base_threshold)
            return max(min_threshold, min(adaptive_threshold, max_threshold))
            
        except Exception as e:
            print(f"Error calculating threshold: {e}, using default")
            return 20

    @staticmethod
    def extract_with_pytesseract(image_path):
        if not os.path.isfile(image_path):
            return None

        try:
            image = ImageProcessor.process_image(image_path)
            if image is not None:
                text = pytesseract.image_to_string(
                    image,
                    config='--oem 3 --psm 6',
                    lang='tur+eng'
                ).strip()
                return text.upper() if text else None
        except Exception as e:
            print(f"Tesseract error: {e}")
        return None

    @staticmethod
    def extract_with_easyocr(image_path):
        try:
            global _easyocr_reader
            image = ImageProcessor.process_image(image_path)
            if image is None:
                return None
                
            if _easyocr_reader is None:
                _easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=False)
            
            results = _easyocr_reader.readtext(image)
            if not results:
                return None

            # Calculate adaptive threshold based on image size
            y_threshold = OCRMethods._calculate_adaptive_threshold(image)

            lines = []
            current_line = []
            last_y = None

            # Sort boxes by y-coordinate first
            sorted_boxes = sorted(results, key=lambda x: sum(point[1] for point in x[0]) / 4)

            for bbox, text, conf in sorted_boxes:
                if conf < 0.3: 
                    continue

                y_coord = sum(point[1] for point in bbox) / 4
                x_coord = sum(point[0] for point in bbox) / 4

                # Start new line if y-coordinate differs significantly
                if last_y is not None and abs(y_coord - last_y) > y_threshold:
                    if current_line:
                        current_line.sort(key=lambda x: x[1])
                        lines.append(' '.join(word[0] for word in current_line))
                        current_line = []

                current_line.append((text, x_coord))
                last_y = y_coord

            if current_line:
                current_line.sort(key=lambda x: x[1])
                lines.append(' '.join(word[0] for word in current_line))

            return '\n'.join(lines).upper() if lines else None
        except Exception as e:
            print(f"EasyOCR error: {e}")
            return None

    @staticmethod
    def extract_with_paddleocr(image_path):
        try:
            global _paddle_ocr
            image = ImageProcessor.process_image(image_path)
            if image is None:
                return None

            if _paddle_ocr is None:
                _paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False, show_log=False)  # Added show_log=False
                
            # Get image dimensions for threshold calculation
            if hasattr(image, 'shape'):
                height = image.shape[0]
            elif isinstance(image, Image.Image):
                height = image.size[1]

            result = _paddle_ocr.ocr(image)
            if not result or not result[0]:
                return None

            y_threshold = OCRMethods._calculate_adaptive_threshold(height)

            lines = []
            current_line = []
            last_y = None

            sorted_boxes = sorted(result[0], key=lambda x: sum(point[1] for point in x[0]) / 4)

            for detection in sorted_boxes:
                bbox, (text, conf) = detection
                if conf < 0.3:
                    continue

                y_coord = sum(point[1] for point in bbox) / 4
                x_coord = sum(point[0] for point in bbox) / 4

                if last_y is not None and abs(y_coord - last_y) > y_threshold:
                    if current_line:
                        current_line.sort(key=lambda x: x[1])
                        lines.append(' '.join(word[0] for word in current_line))
                        current_line = []

                current_line.append((text, x_coord))
                last_y = y_coord

            if current_line:
                current_line.sort(key=lambda x: x[1])
                lines.append(' '.join(word[0] for word in current_line))

            return '\n'.join(lines).upper() if lines else None
        except Exception as e:
            print(f"PaddleOCR error: {e}")
            return None

    @staticmethod
    def extract_with_suryaocr(image_path):
        try:
            image = Image.open(image_path)
            det_processor, det_model = load_det_processor(), load_det_model()
            rec_model, rec_processor = load_rec_model(), load_rec_processor()
            
            predictions = run_ocr([image], [["tr", "en"]], det_model, det_processor, rec_model, rec_processor)
            text = '\n'.join([line.text for page in predictions for line in page.text_lines])
            return text.upper() if text else None
        except:
            return None
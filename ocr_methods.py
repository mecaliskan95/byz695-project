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
        global _easyocr_reader
        image = ImageProcessor.process_image(image_path)
        if image is None:
            return None
            
        if _easyocr_reader is None:
            _easyocr_reader = easyocr.Reader(['en', 'tr'], gpu=False)
        
        results = _easyocr_reader.readtext(image)
        if not results:
            return None

        # Group text by vertical position
        lines = {}
        for (bbox, text, conf) in results:
            if conf < 0.1:  # Skip low confidence results
                continue
                
            # Calculate average y-coordinate of the text box
            y_coord = sum(point[1] for point in bbox) / 4
            # Round to nearest 10 pixels to group nearby lines
            y_bucket = round(y_coord / 10) * 10
            
            # Add text to corresponding line
            if y_bucket not in lines:
                lines[y_bucket] = []
            lines[y_bucket].append(text)

        # Sort by y-coordinate and join each line's text
        sorted_lines = [' '.join(lines[y]) for y in sorted(lines.keys())]
        text = '\n'.join(sorted_lines)
        
        return text.upper() if text else None

    @staticmethod
    def extract_with_paddleocr(image_path):
        global _paddle_ocr
        image = ImageProcessor.process_image(image_path)
        if image is None:
            return None

        if _paddle_ocr is None:
            _paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
            
        result = _paddle_ocr.ocr(image)
        if not result or not result[0]:
            return None

        lines = {}
        for line in result[0]:
            if line[1][1] < 0.5:  # confidence threshold
                continue
            y_coord = sum(point[1] for point in line[0]) / 4
            y_bucket = round(y_coord / 10) * 10
            lines.setdefault(y_bucket, []).append(line[1][0])

        sorted_lines = [' '.join(lines[y]) for y in sorted(lines.keys())]
        return '\n'.join(sorted_lines).upper() if sorted_lines else None

    @staticmethod
    def extract_with_llamaocr(image_path):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            result = subprocess.run(
                ['node', 'app.js', image_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                cwd=current_dir
            )
            return result.stdout.strip().upper() if result.returncode == 0 else None
        except:
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

    @staticmethod
    def batch_process_ocr(image_paths, method_name):
        method = getattr(OCRMethods, f'extract_with_{method_name.lower()}')
        return [method(image_path) for image_path in image_paths if os.path.isfile(image_path)]
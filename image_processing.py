import cv2
import pytesseract
import base64
from skimage.filters import threshold_local

class ImageProcessor:    
    @staticmethod
    def process_image(image_path: str):
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        T = threshold_local(gray, 21, offset=5, method="gaussian")
        return (gray > T).astype("uint8") * 255

    @staticmethod
    def get_image_base64(image_path: str) -> str:
        image = cv2.imread(image_path)
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    @staticmethod
    def extract_text(image_path: str) -> str:
        return pytesseract.image_to_string(
            ImageProcessor.process_image(image_path), 
            lang='tur+eng'
        ).upper()
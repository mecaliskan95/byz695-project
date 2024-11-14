import cv2
import pytesseract
import base64

class ImageProcessor:    
    @staticmethod
    def process_image(image_path: str):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return gray

    @staticmethod
    def get_image_base64(image_path: str) -> str:
        image = cv2.imread(image_path)
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    @staticmethod
    def extract_text(image_path: str) -> str:
        processed_image = ImageProcessor.process_image(image_path)
        return pytesseract.image_to_string(processed_image, lang='tur+eng').upper()
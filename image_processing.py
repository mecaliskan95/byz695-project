import cv2
import pytesseract

class ImageProcessor:    
    @staticmethod
    def process_image(image_path):
        image = cv2.imread(image_path)
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    @staticmethod
    def extract_text(image_path):
        text = pytesseract.image_to_string(
            ImageProcessor.process_image(image_path), 
            lang='tur+eng'
        ).upper()
        return text
import cv2
from skimage.filters import threshold_local
import pytesseract
import logging

def bw_scanner(image):
    """Convert color image to binary using adaptive thresholding."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        T = threshold_local(gray, 21, offset=5, method="gaussian")
        return (gray > T).astype("uint8") * 255
    except Exception as e:
        logging.error(f"Error in bw_scanner: {e}")
        return None

class ImageProcessor:
    """Handles OCR preprocessing and text extraction pipeline."""
    
    @staticmethod
    def preprocess_image(image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Image not found or unable to read")
            bw_image = bw_scanner(image)
            if bw_image is None:
                raise ValueError("Error in converting image to binary")
            contours, _ = cv2.findContours(bw_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 30 and h > 10:
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            return image
        except Exception as e:
            logging.error(f"Error in preprocess_image: {e}")
            return None

    @staticmethod
    def extract_text(image_path):
        try:
            processed_image = ImageProcessor.preprocess_image(image_path)
            if processed_image is None:
                raise ValueError("Error in preprocessing image")
            rgb_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)
            text = pytesseract.image_to_string(rgb_image, lang='tur+eng').upper()
            logging.info(f"Extracted text: {text}")
            return text
        except Exception as e:
            logging.error(f"Error extracting text: {e}")
            return ""
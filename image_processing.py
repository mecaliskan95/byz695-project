import cv2
import numpy as np
from skimage.filters import threshold_local
import pytesseract
from typing import Optional
import base64

def bw_scanner(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    T = threshold_local(gray, 21, offset=5, method="gaussian")
    return (gray > T).astype("uint8") * 255

class ImageProcessor:    
    @staticmethod
    def preprocess_image(image_path: str) -> Optional[np.ndarray]:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Unable to read image: {image_path}")
        return image

    @staticmethod
    def get_processed_image_base64(image_path: str) -> str:
        processed_image = ImageProcessor.preprocess_image(image_path)
        if processed_image is None:
            raise ValueError("Image preprocessing failed")
        _, buffer = cv2.imencode('.jpg', processed_image)
        return base64.b64encode(buffer).decode('utf-8')

    @staticmethod
    def extract_text(image_path: str) -> str:
        processed_image = ImageProcessor.preprocess_image(image_path)
        if processed_image is None:
            raise ValueError("Image preprocessing failed")
        return pytesseract.image_to_string(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB), lang='tur+eng').upper()
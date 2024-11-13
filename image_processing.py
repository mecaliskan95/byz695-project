import cv2
import numpy as np
from skimage.filters import threshold_local
import pytesseract
from typing import Optional

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
            
        bw_image = bw_scanner(image)
        contours, _ = cv2.findContours(bw_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30 and h > 10:
                cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
        return image

    @staticmethod
    def extract_text(image_path: str) -> str:
        processed_image = ImageProcessor.preprocess_image(image_path)
        if processed_image is None:
            raise ValueError("Image preprocessing failed")
            
        return pytesseract.image_to_string(cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB), lang='tur+eng').upper()
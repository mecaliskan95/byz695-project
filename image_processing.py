import cv2
import numpy as np
import os

class ImageProcessor:    
    @staticmethod
    def process_image(image_path):
        if not os.path.exists(image_path):
            return None
            
        image = cv2.imread(image_path)
        if image is None or len(image.shape) < 2:
            return None
            
        # Convert to grayscale if needed
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply erosion
        kernel = np.ones((3, 3), np.uint8)
        result = cv2.erode(enhanced, kernel, iterations=1)
        
        return result
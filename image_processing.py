import cv2
import numpy as np
import os

class ImageProcessor:    
    @staticmethod
    def process_image(image_path):
        # Existing code (commented out)
        # image = cv2.imread(image_path)
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        # clahe_image = clahe.apply(gray)
        # kernel = np.ones((3, 3), np.uint8)
        # image = cv2.erode(clahe_image, kernel, iterations=1)
        # return image

        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Auto-level (Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_image = clahe.apply(gray)
        
        # Sharpen
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(clahe_image, -1, kernel)
        
        # Contrast adjustment
        alpha = 1.5  # Simple contrast control
        beta = 0     # Simple brightness control
        contrast_adjusted = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
        
        return contrast_adjusted
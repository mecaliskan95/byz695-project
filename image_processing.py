import cv2
import numpy as np
import os

class ImageProcessor:    
    @staticmethod
    def process_image(image_path):

        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        clahe_image = clahe.apply(gray)
        
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened = cv2.filter2D(clahe_image, -1, kernel)
        
        alpha = 1.5
        beta = 0 
        contrast_adjusted = cv2.convertScaleAbs(sharpened, alpha=alpha, beta=beta)
        
        return contrast_adjusted
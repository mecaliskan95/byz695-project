import cv2
import numpy as np
import os
from PIL import Image

class ImageProcessor:    
    @staticmethod
    def process_image(image_path):
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        # clahe_image = clahe.apply(gray)
        
        # kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        # sharpened = cv2.filter2D(clahe_image, -1, kernel)
        
        # contrast_adjusted = cv2.convertScaleAbs(sharpened, alpha=1.5, beta=0)
        
        # return contrast_adjusted
        return gray

    '''
    @staticmethod
    def upscale_image(image_path, scale_factor=2):
        import tensorflow as tf
        
        image = tf.io.read_file(image_path)
        image = tf.image.decode_image(image)
        
        new_size = [
            int(image.shape[0] * scale_factor), 
            int(image.shape[1] * scale_factor)
        ]
        
        upscaled = tf.image.resize(image, new_size, method='bicubic')
        
        upscaled = tf.cast(upscaled, tf.uint8)
        
        output_path = os.path.splitext(image_path)[0] + '_upscaled.jpg'
        
        tf.io.write_file(output_path, tf.image.encode_jpeg(upscaled))
        return output_path
    '''
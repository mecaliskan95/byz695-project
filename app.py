pip install pytesseract pillow opencv-python flask

import pytesseract
from PIL import Image
import cv2
import re
import os

# Set the path to the Tesseract executable if needed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

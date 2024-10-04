# pip install pillow
# pip install pytesseract

from PIL import Image
import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

image = Image.open("ocr-tesseract-sample-text.png")
text = pytesseract.image_to_string(image)

print(text)
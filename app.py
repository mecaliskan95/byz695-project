# pip install pillow
# pip install pytesseract

from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"c:\Users\mertc\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Load the invoice image
image = Image.open("Capture2.PNG")
text = pytesseract.image_to_string(image)

print(text)
print(type(text))

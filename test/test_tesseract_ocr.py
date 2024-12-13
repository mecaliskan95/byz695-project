import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr_methods import OCRMethods
from text_extraction import TextExtractor

def test_tesseract_ocr(image_path):
    print(f"\n{'='*80}\nTesting Tesseract OCR on: {os.path.basename(image_path)}\n{'='*80}")
    
    raw_text = OCRMethods.extract_with_pytesseract(image_path)
    print("\nRaw Extracted Text:")
    print(raw_text if raw_text else "No text extracted")
    
    if raw_text:
        corrected_text = TextExtractor.correct_text(raw_text)
        print("\nCorrected Text:")
        print(corrected_text)
        
        print("\nExtracted Fields:")
        print("-" * 40)
        date = TextExtractor.extract_date(corrected_text)
        time = TextExtractor.extract_time(corrected_text)
        tax_office = TextExtractor.extract_tax_office_name(corrected_text)
        tax_number = TextExtractor.extract_tax_office_number(corrected_text)
        total = TextExtractor.extract_total_cost(corrected_text)
        vat = TextExtractor.extract_vat(corrected_text)
        payment = TextExtractor.extract_payment_method(corrected_text)

        print(f"Date: {date}")
        print(f"Time: {time}")
        print(f"Tax Office: {tax_office}")
        print(f"Tax Number: {tax_number}")
        print(f"Total Cost: {total}")
        print(f"VAT: {vat}")
        print(f"Payment Method: {payment}")

def main():
    test_data_path = os.path.join(os.path.dirname(__file__), 'test_data')
    
    if not os.path.exists(test_data_path):
        print(f"Creating test data directory at: {test_data_path}")
        os.makedirs(test_data_path)
        print("Please add your test images to the test_data folder and run the script again.")
        return
    
    image_files = [
        os.path.join(test_data_path, f) 
        for f in os.listdir(test_data_path) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))
    ]
    
    if not image_files:
        print("No image files found in test_data folder.")
        return
    
    for image_path in image_files:
        test_tesseract_ocr(image_path)

if __name__ == "__main__":
    main()
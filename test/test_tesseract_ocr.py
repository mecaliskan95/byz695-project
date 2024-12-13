import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr_methods import OCRMethods
from text_extraction import TextExtractor

def export_statistics(stats, ocr_name):
    """Export test statistics to a log file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'{ocr_name}_stats_{timestamp}.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Test Results for {ocr_name}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        f.write(f"Total images processed: {stats['total_images']}\n")
        f.write(f"OCR Success Rate: {((stats['ocr_attempts'] - stats['ocr_failures'])/stats['ocr_attempts']*100):.2f}%\n")
        f.write(f"OCR Failed: {stats['ocr_failures']} of {stats['ocr_attempts']} attempts\n")
        f.write(f"Total fields processed: {stats['total_fields']}\n")
        f.write(f"Successful extractions: {stats['successful_extractions']}\n")
        f.write(f"Failed extractions (N/A): {stats['failed_extractions']}\n")
        f.write(f"Success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%\n")
    
    print(f"\nStatistics exported to: {log_file}")

def test_tesseract_ocr(image_path, stats):
    print(f"\n{'='*80}\nTesting Tesseract OCR on: {os.path.basename(image_path)}\n{'='*80}")
    
    raw_text = OCRMethods.extract_with_pytesseract(image_path)
    print("\nRaw Extracted Text:")
    print(raw_text if raw_text else "No text extracted")
    
    # Update OCR success/failure statistics
    stats['ocr_attempts'] += 1
    
    # Number of fields we expect to extract
    expected_fields = 7  # Date, Time, Tax Office, Tax Number, Total Cost, VAT, Payment Method
    
    if not raw_text:
        stats['ocr_failures'] += 1
        stats['total_fields'] += expected_fields
        stats['failed_extractions'] += expected_fields
        print("OCR failed to read the image - counting all fields as failed")
        return
    
    # Rest of processing for successful OCR
    corrected_text = TextExtractor.correct_text(raw_text)
    print("\nCorrected Text:")
    print(corrected_text)
    
    print("\nExtracted Fields:")
    print("-" * 40)
    fields = {
        "Date": TextExtractor.extract_date(corrected_text),
        "Time": TextExtractor.extract_time(corrected_text),
        "Tax Office": TextExtractor.extract_tax_office_name(corrected_text),
        "Tax Number": TextExtractor.extract_tax_office_number(corrected_text),
        "Total Cost": TextExtractor.extract_total_cost(corrected_text),
        "VAT": TextExtractor.extract_vat(corrected_text),
        "Payment Method": TextExtractor.extract_payment_method(corrected_text)
    }
    
    # Update statistics
    for field_name, value in fields.items():
        stats['total_fields'] += 1
        if value != "N/A":
            stats['successful_extractions'] += 1
        else:
            stats['failed_extractions'] += 1

    # Print fields
    for field_name, value in fields.items():
        print(f"{field_name}: {value}")

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

    # Initialize statistics with new counters
    stats = {
        'total_images': len(image_files),
        'ocr_attempts': 0,
        'ocr_failures': 0,
        'total_fields': 0,
        'successful_extractions': 0,
        'failed_extractions': 0
    }
    
    for image_path in image_files:
        test_tesseract_ocr(image_path, stats)

    # Print enhanced final statistics
    print("\n" + "="*80)
    print("FINAL STATISTICS:")
    print(f"Total images processed: {stats['total_images']}")
    print(f"OCR Success Rate: {((stats['ocr_attempts'] - stats['ocr_failures'])/stats['ocr_attempts']*100):.2f}%")
    print(f"OCR Failed: {stats['ocr_failures']} of {stats['ocr_attempts']} attempts")
    print(f"Total fields attempted: {stats['total_fields']}")
    print(f"Successful extractions: {stats['successful_extractions']}")
    print(f"Failed extractions (N/A): {stats['failed_extractions']}")
    print(f"Overall success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%")
    print("="*80)
    
    # Export statistics
    export_statistics(stats, "Tesseract")

if __name__ == "__main__":
    main()
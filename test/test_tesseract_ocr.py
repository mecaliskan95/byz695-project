import os
import sys
from datetime import datetime
import random
import time
import csv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from text_extraction import TextExtractor
from ocr_methods import OCRMethods

def log_output(message, file, separator=None):
    if separator:
        sep_line = separator * 80 if separator == '=' else separator * 40
        file.write(sep_line + "\n")
    
    if message is not None:
        file.write(str(message) + "\n")

def export_statistics(stats, ocr_name, all_texts=None):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'{ocr_name}_stats_{timestamp}.txt')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Test Results for {ocr_name}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*50 + "\n\n")
        f.write("STATISTICS:\n")
        f.write("-"*20 + "\n")
        f.write(f"Total images processed: {stats['total_images']}\n")
        f.write(f"OCR Success Rate: {((stats['ocr_attempts'] - stats['ocr_failures'])/stats['ocr_attempts']*100):.2f}%\n")
        f.write(f"OCR Failed: {stats['ocr_failures']} of {stats['ocr_attempts']} attempts\n")
        f.write(f"Total fields processed: {stats['total_fields']}\n")
        f.write(f"Successful extractions: {stats['successful_extractions']}\n")
        f.write(f"Failed extractions (N/A): {stats['failed_extractions']}\n")
        f.write(f"Success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%\n\n")
        
        if all_texts:
            f.write("\nPROCESSED OUTPUTS:\n")
            f.write("="*50 + "\n\n")
            for filename, text in all_texts.items():
                f.write(f"\nFile: {filename}\n")
                f.write("-"*50 + "\n")
                f.write(f"Output Text:\n{text}\n")
                f.write("-"*50 + "\n")
    
    print(f"\nResults exported to: {log_file}")

def test_tesseract_ocr(image_path, stats, log_file):
    log_output(f"\nTesting Tesseract OCR on: {os.path.basename(image_path)}", log_file, "=")
    
    ocr = OCRMethods() 
    raw_text = ocr.extract_with_pytesseract(image_path)
    stats['ocr_attempts'] += 1
    
    if not raw_text:
        stats['ocr_failures'] += 1
        stats['total_fields'] += 7
        stats['failed_extractions'] += 7
        log_output("OCR failed to read the image - counting all fields as failed", log_file)
        return None

    output_text = TextExtractor.correct_text(raw_text)
    log_output("\nProcessed Text Output:", log_file, "-")
    log_output(output_text, log_file)
    
    fields = {
        "filename": os.path.basename(image_path),
        "date": TextExtractor.extract_date(output_text),
        "time": TextExtractor.extract_time(output_text),
        "tax_office_name": TextExtractor.extract_tax_office_name(output_text),
        "tax_office_number": TextExtractor.extract_tax_office_number(output_text),
        "total_cost": TextExtractor.extract_total_cost(output_text),
        "vat": TextExtractor.extract_vat(output_text),
        "payment_method": TextExtractor.extract_payment_method(output_text)
    }
    
    log_output("\nExtracted Fields:", log_file, "-")
    for field_name, value in fields.items():
        stats['total_fields'] += 1
        success = value != "N/A"
        stats['successful_extractions' if success else 'failed_extractions'] += 1
        log_output(f"{field_name}: {value} {'✓' if success else '✗'}", log_file)
    log_output("", log_file, "-")

    return output_text, fields

def main():
    start_time = time.time()
    uploads_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    
    if not os.path.exists(uploads_path):
        print(f"Uploads directory not found at: {uploads_path}")
        return
    
    image_files = [
        os.path.join(uploads_path, f) 
        for f in os.listdir(uploads_path) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp'))
    ]
    
    if not image_files:
        print("No image files found in uploads folder.")
        return

    ocr = OCRMethods()
    TextExtractor.set_testing_mode(True, ocr.extract_with_pytesseract)
    
    stats = {
        'total_images': len(image_files),
        'ocr_attempts': 0,
        'ocr_failures': 0,
        'total_fields': 0,
        'successful_extractions': 0,
        'failed_extractions': 0
    }
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'Tesseract_stats_{timestamp}.txt')
    csv_file = os.path.join(log_dir, f'Tesseract_data_{timestamp}.csv')
    
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number', 
                        'Total Cost', 'VAT', 'Payment Method'])

    with open(log_file, 'w', encoding='utf-8') as f:
        all_texts = {}
        all_fields = []
        
        for image_path in image_files:
            output_text, fields = test_tesseract_ocr(image_path, stats, f)
            if output_text:
                all_texts[os.path.basename(image_path)] = output_text
                all_fields.append(fields)

        with open(csv_file, 'a', newline='', encoding='utf-8-sig') as csvf:
            writer = csv.writer(csvf)
            for fields in all_fields:
                writer.writerow([
                    fields['filename'],
                    fields['date'],
                    fields['time'],
                    fields['tax_office_name'],
                    fields['tax_office_number'],
                    fields['total_cost'],
                    fields['vat'],
                    fields['payment_method']
                ])

        log_output("\nFINAL STATISTICS:", f, "=")
        log_output(f"Total images processed: {stats['total_images']}", f)
        log_output(f"OCR Success Rate: {((stats['ocr_attempts'] - stats['ocr_failures'])/stats['ocr_attempts']*100):.2f}%", f)
        log_output(f"OCR Failed: {stats['ocr_failures']} of {stats['ocr_attempts']} attempts", f)
        log_output(f"Total fields attempted: {stats['total_fields']}", f)
        log_output(f"Successful extractions: {stats['successful_extractions']}", f)
        log_output(f"Failed extractions (N/A): {stats['failed_extractions']}", f)
        log_output(f"Overall success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%", f)
        
        elapsed_time = time.time() - start_time
        log_output(f"Total execution time: {elapsed_time:.2f} seconds", f)
        log_output("", f, "=")
        
    print(f"\nResults exported to:")
    print(f"Log file: {log_file}")
    print(f"CSV file: {csv_file}")

if __name__ == "__main__":
    main()
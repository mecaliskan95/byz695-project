import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ocr_methods import OCRMethods
from text_extraction import TextExtractor

def log_output(message, file, separator=None):
    """Write to log file with optional separator"""
    if separator:
        sep_line = separator * 80 if separator == '=' else separator * 40
        file.write(sep_line + "\n")
    
    if message is not None:
        file.write(str(message) + "\n")

def export_statistics(stats, ocr_name, all_results=None):
    """Export test statistics and all results to a log file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'{ocr_name}_stats_{timestamp}.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        log_output(f"Test Results for {ocr_name}", f)
        log_output(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f)
        log_output("", f, "=")

        # Write statistics
        log_output("STATISTICS:", f)
        log_output("", f, "-")
        log_output(f"Total images processed: {stats['total_images']}", f)
        log_output(f"OCR Success Rate: {((stats['ocr_attempts'] - stats['ocr_failures'])/stats['ocr_attempts']*100):.2f}%", f)
        log_output(f"OCR Failed: {stats['ocr_failures']} of {stats['ocr_attempts']} attempts", f)
        log_output(f"Total fields processed: {stats['total_fields']}", f)
        log_output(f"Successful extractions: {stats['successful_extractions']}", f)
        log_output(f"Failed extractions (N/A): {stats['failed_extractions']}", f)
        log_output(f"Success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%", f)
        
        # Write results
        if all_results:
            for filename, result in all_results.items():
                log_output(f"\nFile: {filename}", f)
                log_output("", f, "-")
                
                log_output("Processed Text:", f)
                log_output(result['text'], f)
                log_output("", f, "-")
                
                log_output("Extracted Fields:", f)
                for field_name, value in result['fields'].items():
                    success = "✓" if value != "N/A" else "✗"
                    log_output(f"{field_name}: {value} {success}", f)
                log_output("", f, "-")

def test_llama_ocr(image_path, stats, log_file):
    log_output(f"\nTesting LlamaOCR on: {os.path.basename(image_path)}", log_file, "=")
    
    raw_text = OCRMethods.extract_with_llamaocr(image_path)
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
        "Date": TextExtractor.extract_date(output_text),
        "Time": TextExtractor.extract_time(output_text),
        "Tax Office": TextExtractor.extract_tax_office_name(output_text),
        "Tax Number": TextExtractor.extract_tax_office_number(output_text),
        "Total Cost": TextExtractor.extract_total_cost(output_text),
        "VAT": TextExtractor.extract_vat(output_text),
        "Payment Method": TextExtractor.extract_payment_method(output_text)
    }
    
    log_output("\nExtracted Fields:", log_file, "-")
    for field_name, value in fields.items():
        stats['total_fields'] += 1
        success = value != "N/A"
        stats['successful_extractions' if success else 'failed_extractions'] += 1
        log_output(f"{field_name}: {value} {'✓' if success else '✗'}", log_file)
    log_output("", log_file, "-")

    return output_text

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
    log_file = os.path.join(log_dir, f'LlamaOCR_stats_{timestamp}.log')
    
    with open(log_file, 'w', encoding='utf-8') as f:
        all_texts = {}
        for image_path in image_files:
            output_text = test_llama_ocr(image_path, stats, f)
            if output_text:
                all_texts[os.path.basename(image_path)] = output_text
        
        # Write final statistics
        log_output("\nFINAL STATISTICS:", f, "=")
        log_output(f"Total images processed: {stats['total_images']}", f)
        log_output(f"OCR Success Rate: {((stats['ocr_attempts'] - stats['ocr_failures'])/stats['ocr_attempts']*100):.2f}%", f)
        log_output(f"OCR Failed: {stats['ocr_failures']} of {stats['ocr_attempts']} attempts", f)
        log_output(f"Total fields processed: {stats['total_fields']}", f)
        log_output(f"Successful extractions: {stats['successful_extractions']}", f)
        log_output(f"Failed extractions (N/A): {stats['failed_extractions']}", f)
        log_output(f"Success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%", f)
        log_output("", f, "=")
        
    print(f"\nResults exported to: {log_file}")

if __name__ == "__main__":
    main()

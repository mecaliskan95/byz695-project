import os
import sys
from datetime import datetime
import time
import argparse
import psutil
import json
import csv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from text_extraction import TextExtractor
from ocr_methods import OCRMethods
from app import track_resources

def log_output(message, file, separator=None):
    if separator:
        sep_line = separator * 80 if separator == '=' else separator * 40
        file.write(sep_line + "\n")
    if message is not None:
        file.write(str(message) + "\n")

def calculate_field_accuracy(stats):
    field_stats = {
        'date': {'success': 0, 'total': 0},
        'time': {'success': 0, 'total': 0},
        'tax_office_name': {'success': 0, 'total': 0},
        'tax_office_number': {'success': 0, 'total': 0},
        'total_cost': {'success': 0, 'total': 0},
        'vat': {'success': 0, 'total': 0},
        'payment_method': {'success': 0, 'total': 0}
    }
    return {
        field: {
            'accuracy': (stats[field]['success'] / stats[field]['total'] * 100) if stats[field]['total'] > 0 else 0,
            'success': stats[field]['success'],
            'total': stats[field]['total']
        }
        for field in field_stats
    }

def test_ocr_method(image_path, method_name, ocr_method, stats, log_file):
    method_start_time = time.time()
    method_start_cpu = psutil.cpu_percent()
    process = psutil.Process()
    method_start_memory = process.memory_info().rss / 1024 / 1024
    
    log_output(f"\nTesting {method_name} on: {os.path.basename(image_path)}", log_file, "=")
    
    raw_text = ocr_method(image_path)
    stats['ocr_attempts'] += 1
    
    if not raw_text:
        stats['ocr_failures'] += 1
        stats['total_fields'] += 7
        stats['failed_extractions'] += 7
        log_output(f"{method_name} failed to read the image - counting all fields as failed", log_file)
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
    
    fields['total_cost'], fields['vat'] = TextExtractor.validate_total_cost_and_vat(
        fields['total_cost'], fields['vat']
    )
    
    log_output("\nExtracted Fields:", log_file, "-")
    for field_name, value in fields.items():
        if field_name != "filename":
            stats['total_fields'] += 1
            success = value != "N/A"
            stats['successful_extractions' if success else 'failed_extractions'] += 1
        log_output(f"{field_name}: {value} {'✓' if value != 'N/A' else '✗'}", log_file)
    
    for field_name, value in fields.items():
        if field_name != "filename": 
            if field_name not in stats['field_stats']:
                stats['field_stats'][field_name] = {'success': 0, 'total': 0}
            stats['field_stats'][field_name]['total'] += 1
            if value != "N/A":
                stats['field_stats'][field_name]['success'] += 1

    log_output("", log_file, "-")

    method_end_time = time.time()
    method_end_memory = process.memory_info().rss / 1024 / 1024
    method_cpu_usage = psutil.cpu_percent() - method_start_cpu
    
    stats['execution_time'] = method_end_time - method_start_time
    stats['cpu_usage'] = method_cpu_usage
    stats['memory_used'] = method_end_memory - method_start_memory
    
    return output_text, fields

def test_single_file(filename):
    update_resources, get_resource_stats = track_resources()
    
    TextExtractor.initialize_tax_office_mapping()
    
    start_time = time.time()
    start_cpu_percent = psutil.cpu_percent()
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    uploads_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    image_path = os.path.join(uploads_path, filename)
    
    if not os.path.exists(image_path):
        print(f"File not found: {filename}")
        return

    log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f'all_ocr_methods_{filename}_{timestamp}.txt')
    csv_file = os.path.join(log_dir, f'all_ocr_methods_{filename}_{timestamp}.csv')
    
    ocr_methods = {
        'PaddleOCR': OCRMethods.extract_with_paddleocr,
        'EasyOCR': OCRMethods.extract_with_easyocr,
        'Tesseract': OCRMethods.extract_with_pytesseract,
        'SuryaOCR': OCRMethods.extract_with_suryaocr
    }
    
    with open(log_file, 'w', encoding='utf-8') as f:
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as csvf:
            writer = csv.writer(csvf)
            writer.writerow(['Method', 'Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number', 
                           'Total Cost', 'VAT', 'Payment Method'])

            log_output(f"Test Results for {filename}", f, "=")
            log_output(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", f)
            log_output("", f, "=")

            all_stats = {}
            all_texts = {}
            all_fields = {}

            for method_name, ocr_method in ocr_methods.items():
                stats = {
                    'ocr_attempts': 0,
                    'ocr_failures': 0,
                    'total_fields': 0,
                    'successful_extractions': 0,
                    'failed_extractions': 0,
                    'execution_time': 0,
                    'cpu_usage': 0,
                    'memory_used': 0,
                    'field_stats': {}
                }
                
                update_resources()
                output_text, fields = test_ocr_method(image_path, method_name, ocr_method, stats, f)
                update_resources()
                
                if output_text:
                    all_texts[method_name] = output_text
                    all_fields[method_name] = fields
                    writer.writerow([
                        method_name,
                        fields['filename'],
                        fields['date'],
                        fields['time'],
                        fields['tax_office_name'],
                        fields['tax_office_number'],
                        fields['total_cost'],
                        fields['vat'],
                        fields['payment_method']
                    ])
                all_stats[method_name] = stats

                log_output(f"\nField-Level Accuracy for {method_name}:", f, "-")
                for field_name, stats in stats['field_stats'].items():
                    accuracy = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                    log_output(f"{field_name}: {accuracy:.2f}% ({stats['success']}/{stats['total']})", f)

            resource_stats = get_resource_stats()
            log_output("\nFINAL STATISTICS", f, "=")
            for method_name, stats in all_stats.items():
                log_output(f"\n{method_name}:", f)
                log_output(f"Total fields attempted: {stats['total_fields']}", f)
                log_output(f"Successful extractions: {stats['successful_extractions']}", f)
                log_output(f"Failed extractions (N/A): {stats['failed_extractions']}", f)
                log_output(f"Success rate: {(stats['successful_extractions']/stats['total_fields']*100):.2f}%", f)
                log_output(f"Execution time: {stats['execution_time']:.2f} seconds", f)
                log_output(f"Average CPU Usage: {resource_stats['cpu_avg']:.2f}%", f)
                log_output(f"Peak CPU Usage: {resource_stats['cpu_max']:.2f}%", f)
                log_output(f"Average Memory Usage: {resource_stats['memory_avg']:.2f} MB", f)
                log_output(f"Peak Memory Usage: {resource_stats['memory_max']:.2f} MB", f)

    print(f"\nResults exported to:")
    print(f"Log file: {log_file}")
    print(f"CSV file: {csv_file}")

def natural_sort_key(s):
    import re
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test OCR methods on a single image file.')
    parser.add_argument('input', nargs='?', help='Name or number of the image file to process')
    
    args, unknown = parser.parse_known_args()
    
    if unknown:
        if args.input:
            args.input = args.input + ' ' + ' '.join(unknown)
    
    uploads_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
    image_files = sorted(
        [f for f in os.listdir(uploads_path) 
         if f.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', 'jfif'))],
        key=natural_sort_key
    )
    
    if not image_files:
        print("No image files found in uploads folder.")
        sys.exit(1)

    print("\nAvailable files in uploads folder:")
    for i, file in enumerate(image_files, 1):
        print(f"{i}. {file}")

    if args.input:
        matching_files = [f for f in image_files if args.input in f]
        try:
            file_index = int(args.input)
            if 1 <= file_index <= len(image_files):
                test_single_file(image_files[file_index - 1])
            else:
                print(f"Error: Number must be between 1 and {len(image_files)}")
                sys.exit(1)
        except ValueError:
            if len(matching_files) == 1:
                test_single_file(matching_files[0])
            elif len(matching_files) > 1:
                print("\nMultiple matching files found:")
                for i, file in enumerate(matching_files, 1):
                    print(f"{i}. {file}")
                while True:
                    try:
                        choice = int(input("\nEnter the number of the file you want to test: "))
                        if 1 <= choice <= len(matching_files):
                            test_single_file(matching_files[choice - 1])
                            break
                        else:
                            print(f"Invalid choice. Please enter a number between 1 and {len(matching_files)}")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            else:
                print(f"Error: No matching files found for '{args.input}'")
                sys.exit(1)
    else:
        while True:
            choice = input("\nEnter the number or name of the file you want to test: ")
            try:
                file_index = int(choice)
                if 1 <= file_index <= len(image_files):
                    test_single_file(image_files[file_index - 1])
                    break
                else:
                    print(f"Invalid choice. Please enter a number between 1 and {len(image_files)} or a valid filename")
            except ValueError:
                if choice in image_files:
                    test_single_file(choice)
                    break
                else:
                    print("Invalid input. Please enter a valid number or filename")

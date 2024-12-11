from text_extraction import TextExtractor
from config import Config

# Ensure Tesseract command is set
Config()

# Paths to the images you want to test
image_paths = [r"uploads/fatura1.jpg"]
filenames = ["fatura1.jpg"]

# Extract all data
results = TextExtractor.extract_all(image_paths, filenames)

# Print the results
for result in results:
    print(f"Results for {result['filename']}:")
    print(f"  Date: {result['date']} (Method: {result['date_method']})")
    print(f"  Time: {result['time']} (Method: {result['time_method']})")
    print(f"  Tax Office Name: {result['tax_office_name']} (Method: {result['tax_office_name_method']})")
    print(f"  Tax Office Number: {result['tax_office_number']} (Method: {result['tax_office_number_method']})")
    print(f"  Total Cost: {result['total_cost']} (Method: {result['total_cost_method']})")
    print(f"  VAT: {result['vat']} (Method: {result['vat_method']})")
    print(f"  Payment Method: {result['payment_method']} (Method: {result['payment_method_method']})")
    print(f"  LlamaOCR Output: {result['llamaocr_output']} (Method: {result['llamaocr_method']})")
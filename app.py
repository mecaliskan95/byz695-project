import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['KERAS_BACKEND'] = 'tensorflow'

import time
import psutil
import json
from pathlib import Path

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

import csv
from io import StringIO, BytesIO
import tempfile
import shutil
import logging
from flask import Flask, render_template, request, send_file
from text_extraction import TextExtractor
from werkzeug.utils import secure_filename
from ocr_methods import OCRMethods
from datetime import datetime

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'tiff', 'bmp', 'jfif'}

logging.basicConfig(level=logging.WARNING)
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 120 * 1024 * 1024 

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def track_resources():
    cpu_percentages = []
    memory_usage = []
    process = psutil.Process()
    
    def update():
        cpu_percentages.append(psutil.cpu_percent())
        memory_usage.append(process.memory_info().rss / 1024 / 1024)
        
    def get_stats():
        return {
            'cpu_avg': sum(cpu_percentages) / len(cpu_percentages) if cpu_percentages else 0,
            'cpu_max': max(cpu_percentages) if cpu_percentages else 0,
            'memory_avg': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            'memory_max': max(memory_usage) if memory_usage else 0
        }
    return update, get_stats

def save_statistics(stats, results, elapsed_time):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_dir = Path("statistics")
    stats_dir.mkdir(exist_ok=True)
    
    csv_path = stats_dir / f"invoice_data_{timestamp}.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        headers = ['Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number', 'Total Cost', 'VAT', 'Payment Methods']
        writer.writerow(headers)
        fields = ['filename', 'date', 'time', 'tax_office_name', 'tax_office_number', 'total_cost', 'vat', 'payment_method']
        for row in results:
            writer.writerow([str(row.get(field, 'N/A')) for field in fields])

    stats_path = stats_dir / f"invoice_stats_{timestamp}.txt"
    with open(stats_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n\n")
        f.write("FINAL STATISTICS:\n")
        f.write(f"Total images processed: {stats['total_images']}\n")
        f.write(f"Total fields attempted: {stats['total_fields_attempted']}\n")
        f.write(f"Successful extractions: {stats['successful_extractions']}\n")
        f.write(f"Failed extractions (N/A): {stats['failed_extractions']}\n")
        f.write(f"Overall success rate: {stats['success_rate']:.2f}%\n")
        f.write(f"Total execution time: {stats['processing_time']:.2f} seconds\n")
        f.write(f"Average CPU Usage: {stats['avg_cpu_usage']:.2f}%\n")
        f.write(f"Peak CPU Usage: {stats['peak_cpu_usage']:.2f}%\n")
        f.write(f"Average Memory Usage: {stats['avg_memory_usage']:.2f} MB\n")
        f.write(f"Peak Memory Usage: {stats['peak_memory_usage']:.2f} MB\n")
        f.write("\n" + "=" * 80 + "\n")
        
    return csv_path, stats_path

def process_files(files):
    update_resources, get_resource_stats = track_resources()
    start_time = time.time()
    start_cpu_percent = psutil.cpu_percent()
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # Convert to MB
    
    temp_dir = tempfile.mkdtemp()
    try:
        files_info = {'paths': [], 'names': []}
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                files_info['paths'].append(filepath)
                files_info['names'].append(filename)
        
        if not files_info['paths']:
            return None
            
        update_resources()  # Before OCR processing
        results = TextExtractor.extract_all(files_info['paths'], files_info['names'])
        update_resources()  # After OCR processing
        
        # Calculate statistics
        total_fields = len(results) * 7  # 7 fields per result
        successful_extractions = sum(1 for result in results for field in 
            ['date', 'time', 'tax_office_name', 'tax_office_number', 'total_cost', 'vat', 'payment_method']
            if result.get(field) != 'N/A')
        
        elapsed_time = time.time() - start_time
        end_cpu_percent = psutil.cpu_percent()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        resource_stats = get_resource_stats()
        
        stats = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_images': len(files_info['paths']),
            'total_fields_attempted': total_fields,
            'successful_extractions': successful_extractions,
            'failed_extractions': total_fields - successful_extractions,
            'success_rate': round((successful_extractions / total_fields * 100), 2),
            'processing_time': round(elapsed_time, 2),
            'cpu_usage': round(end_cpu_percent - start_cpu_percent, 2),
            'memory_used_mb': round(final_memory - initial_memory, 2),
            'avg_cpu_usage': round(resource_stats['cpu_avg'], 2),
            'peak_cpu_usage': round(resource_stats['cpu_max'], 2),
            'avg_memory_usage': round(resource_stats['memory_avg'], 2),
            'peak_memory_usage': round(resource_stats['memory_max'], 2)
        }
        
        # Save results and stats
        csv_path, stats_path = save_statistics(stats, results, elapsed_time)
        
        # Add paths and stats to results
        results.append({
            'statistics': stats,
            'csv_path': str(csv_path),
            'stats_path': str(stats_path)
        })
        
        return results
        
    except Exception as e:
        app.logger.error(f"Error processing files: {str(e)}")
        return None
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            files = request.files.getlist("files")
            if not files or all(file.filename == '' for file in files):
                return render_template("index.html", error="No files were uploaded")
                
            results = process_files(files)
            if not results:
                return render_template("index.html", error="No valid results were extracted")
            
            # Extract statistics from results
            stats = next((item for item in results if 'statistics' in item), None)
            if stats:
                results.remove(stats)  # Remove stats from results list
                
            return render_template("index.html", results=results, statistics=stats['statistics'] if stats else None)
            
        except Exception as e:
            app.logger.error(f"Error processing files: {str(e)}")
            return render_template("index.html", error=f"Error processing files: {str(e)}")
    return render_template("index.html")

@app.route("/export-csv", methods=["POST"])
def export_csv():
    data = request.get_json()
    if not data:
        return "No data received", 400
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"invoice_data_{timestamp}.csv"
    
    output = StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    headers = ['Filename', 'Date', 'Time', 'Tax Office Name', 'Tax Office Number', 'Total Cost', 'VAT', 'Payment Methods']
    writer.writerow(headers)
    fields = ['filename', 'date', 'time', 'tax_office_name', 'tax_office_number', 'total_cost', 'vat', 'payment_methods']
    for row in data:
        writer.writerow([str(row.get(field, 'N/A')) for field in fields])
    output.seek(0)
    file_data = BytesIO(output.getvalue().encode('utf-8-sig'))
    return send_file(file_data, mimetype='text/csv', as_attachment=True, download_name=filename)

if __name__ == "__main__":
    app.run(debug=True, threaded=False)
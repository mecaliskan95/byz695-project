# Turkish Invoice OCR Scanner

An advanced OCR system that extracts data from Turkish invoices using multiple OCR engines, intelligent text processing, and machine learning techniques.

## 📖 Table of Contents
- [Features](#-features)
- [System Requirements](#-system-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Architecture](#-architecture)
- [OCR Engines](#-ocr-engines)
- [Text Processing](#-text-processing)
- [Data Extraction](#-data-extraction)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Performance](#-performance)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Features

### Multiple OCR Engine Support
- **Tesseract OCR**
  - Language support: Turkish + English
  - Custom configuration options
  - Automatic language detection

- **EasyOCR**
  - GPU acceleration support
  - Vertical text detection
  - Confidence scoring
  - Multi-language support

- **PaddleOCR**
  - Angle classification
  - Line grouping
  - Adaptive thresholding
  - High performance

- **SuryaOCR**
  - Advanced text detection
  - Custom model support
  - Fast processing

### Text Processing
- Turkish character handling
- Fuzzy matching
- Dictionary-based correction
- Pattern matching
- Confidence thresholds
- Line merging algorithms

### Data Extraction
- **Fields Supported:**
  - Invoice Date (multiple formats)
  - Time
  - Tax Office Name (verified against database)
  - Tax Office Number (10-11 digits)
  - Total Cost
  - VAT Amount
  - Payment Method

### Web Interface
- Drag-and-drop file upload
- Batch processing
- Real-time progress tracking
- CSV export
- Result visualization
- Responsive design

## 💻 System Requirements

### Hardware
- CPU: Multi-core processor recommended
- RAM: Minimum 8GB, 16GB recommended
- GPU: Optional, supports NVIDIA CUDA
- Storage: 2GB free space

### Software
- Python 3.9+
- Node.js 14+ (for Llama OCR)
- Tesseract 4.1+
- CUDA Toolkit 11.0+ (optional)

## 🔧 Installation

### 1. Clone Repository
```bash
git clone [repository-url]
cd byz695-project
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR
- Windows: Install from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
- Linux: `sudo apt install tesseract-ocr`
- MacOS: `brew install tesseract`

### 4. Verify Tesseract Installation
Default paths:
```
Windows: C:\Program Files\Tesseract-OCR\tesseract.exe
Linux/Mac: /usr/bin/tesseract
```

## 🚀 Usage

1. **Start Server**
   ```bash
   python app.py
   ```

2. **Access Interface**
   ```
   http://localhost:5000
   ```

3. **Upload Files**
   - Drag and drop files
   - Use file upload button
   - Use folder upload button

4. **Export Results**
   - Click "Export to CSV" button
   - Results include all extracted fields

## 📁 Project Structure

```
byz695-project/
├── app.py              # Flask application & routing
├── ocr_methods.py      # OCR engine implementations
├── text_extraction.py  # Text processing & data extraction
├── image_processing.py # Image preprocessing
├── templates/
│   └── index.html     # Web interface
├── words.dic          # Dictionary for text correction
└── vergidaireleri.txt # Valid tax office list
```

## 🛠️ Technical Details

### OCR Pipeline
1. Image preprocessing (contrast, sharpening)
2. Multiple OCR engine attempts
3. Text correction and validation
4. Pattern matching and data extraction

### Supported File Types
- Images: JPG, JPEG, PNG, TIFF, BMP
- Clean, scanned documents recommended

### Error Handling
- Graceful fallback between OCR engines
- File validation
- Encoding detection for Turkish characters
- Comprehensive error logging

## 🔬 Advanced Features

### Image Processing Pipeline
- **Preprocessing**
  - Dynamic thresholding
  - Noise reduction
  - Contrast enhancement
  - Rotation correction
  - Skew detection & correction
  - Border removal
  - Resolution optimization

### Pattern Recognition
- **Regular Expressions**
  - Custom patterns for Turkish formats
  - Flexible date/time matching
  - Currency format handling
  - Tax number validation

- **Fuzzy Matching**
  - Levenshtein distance calculations
  - Phonetic matching for Turkish
  - Confidence scoring
  - Adaptive thresholds

### Performance Optimization
- **Memory Management**
  - Image size optimization
  - Batch processing
  - Resource cleanup
  - Memory pooling

- **Processing Speed**
  - Multi-threading
  - GPU acceleration
  - Caching mechanisms
  - Lazy loading

### Error Handling
- **Validation Layers**
  - Input validation
  - Format verification
  - Data consistency checks
  - Output normalization

- **Recovery Mechanisms**
  - Fallback OCR engines
  - Alternative pattern matching
  - Error logging & reporting
  - Automatic retries

## 📊 Performance Metrics

### OCR Engine Comparison
| Engine      | Speed | Accuracy | Memory Usage | GPU Support |
|-------------|-------|----------|--------------|-------------|
| Tesseract   | ★★★☆☆ | ★★★★☆    | ★★★★★       | ❌          |
| EasyOCR     | ★★★★☆ | ★★★★☆    | ★★★☆☆       | ✅          |
| PaddleOCR   | ★★★★★ | ★★★★★    | ★★★☆☆       | ✅          |
| SuryaOCR    | ★★★★☆ | ★★★★☆    | ★★★★☆       | ✅          |

### Field Extraction Success Rates
- Date: ~95%
- Time: ~90%
- Tax Office: ~85%
- Total Cost: ~98%
- VAT: ~95%
- Payment Method: ~85%

## 🔧 Configuration Options

### OCR Settings

## 🧪 Testing

### Test Suite Overview
The project includes comprehensive test suites for each OCR engine:
- `test_tesseract_ocr.py`
- `test_paddle_ocr.py`
- `test_easy_ocr.py`
- `test_surya_ocr.py`
- `test_llama_ocr.py`

### Running Tests
```
## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📧 Contact

For support or queries: mecaliskan95@gmail.com

# Turkish Invoice OCR Scanner

An advanced OCR application that extracts data from Turkish invoices using multiple OCR engines and intelligent text processing.

## 🎯 Key Features

- **Multi-Engine OCR Processing**
  - Tesseract OCR
  - EasyOCR (with GPU support)
  - PaddleOCR
  - SuryaOCR
  - Fallback mechanism between engines

- **Advanced Text Processing**
  - Turkish language support
  - Fuzzy matching for tax office validation
  - Pattern matching for data extraction
  - Automatic text correction
  - Dictionary-based validation

- **Modern Web Interface**
  - Drag-and-drop file upload
  - Folder upload support
  - Real-time processing status
  - Bilingual interface (EN/TR)
  - CSV export functionality

- **Data Extraction Fields**
  - Tax office name and number
  - Invoice date and time
  - Total cost
  - VAT amount
  - Payment method

## 🔧 Installation

1. **Clone Repository**
   ```bash
   git clone [repository-url]
   cd byz695-project
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**
   - Windows: Install from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt install tesseract-ocr`
   - MacOS: `brew install tesseract`

4. **Verify Tesseract Installation**
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

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📧 Contact

For support or queries: mecaliskan05@gmail.com

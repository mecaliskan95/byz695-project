# Invoice Scanner

A web-based tool that extracts key information from Turkish invoices using OCR technology. The application supports multiple file uploads and provides a clean interface to view extracted data.

## Features

- Extract invoice data including:
  - Date and time
  - Tax office name and number
  - Total cost and VAT
  - Payment methods
- Support for multiple file formats (JPG, JPEG, PNG)
- Folder upload support
- Drag and drop interface
- Bilingual support (English/Turkish)
- Raw text output viewing
- Responsive design

## Prerequisites

- Python 3.8+
- Tesseract OCR ([Download](https://github.com/UB-Mannheim/tesseract/wiki))
- Turkish and English language data for Tesseract

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/byz695-project.git
cd byz695-project
```

2. Install required Python packages:
```
pip install -r requirements.txt
```

3. Configure Tesseract path in config.py:
```
TESSERACT_CMD = Path(r'c:\Program Files\Tesseract-OCR\tesseract.exe')
```

## Usage

1. Start the Flask application:
```
python app.py
```
2. Open a web browser and navigate to:
```
http://localhost:5000
```
3. Upload invoice images through the web interface using either:
  File upload button
  Folder upload button
  Drag and drop

## Project Structure

```
byz695-project/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── image_processing.py   # Image processing utilities
├── text_extraction.py    # Text extraction logic
├── requirements.txt      # Python dependencies
├── vergidaireleri.txt   # List of valid tax offices
└── templates/
    └── index.html       # Web interface template
```

## Text Extraction Features

The application extracts the following information from invoices:

- Date (DD/MM/YYYY format)
- Time (HH:MM format)
- Tax office name (validated against vergidaireleri.txt)
- Tax office number (10-digit format)
- Total cost
- VAT amount
- Payment method

## Acknowledgments

- Tesseract OCR for text recognition
- Flask for the web framework
- OpenCV for image processing

# Invoice Scanner

A web-based tool that extracts key information from Turkish invoices using OCR technology. The application supports multiple file uploads and provides a clean interface to view extracted data.

## Features

- Extract invoice data including:
  - Date and time
  - Tax office name and number
  - Total cost and VAT
  - Payment methods
- Support for multiple file formats (JPG, JPEG, PNG, PDF, ZIP)
- Folder upload support
- Drag and drop interface
- Bilingual support (English/Turkish)
- Raw text output viewing
- Responsive design

## Prerequisites

- Python 3.8+
- Tesseract OCR ([Download](https://github.com/UB-Mannheim/tesseract/wiki))
- EasyOCR ([Installation](https://github.com/JaidedAI/EasyOCR#installation))
- Turkish and English language data for Tesseract and EasyOCR
- CUDA-compatible GPU (optional, for faster processing)
- At least 4GB RAM

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/byz695-project.git
    cd byz695-project
    ```

2. Install required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure Tesseract path in `config.py`:
    ```python
    TESSERACT_CMD = Path(r'c:\Program Files\Tesseract-OCR\tesseract.exe')
    ```

## Configuration

1. Verify Tesseract installation:
    ```sh
    tesseract --version
    ```

2. Ensure language data is installed:
    ```sh
    tesseract --list-langs
    ```
   Should show both 'eng' and 'tur'

3. Test CUDA availability (optional):
    ```python
    import torch
    print(torch.cuda.is_available())
    ```

## Usage

1. Start the Flask application:
    ```sh
    python app.py
    ```

2. Open a web browser and navigate to:
    ```
    http://localhost:5000
    ```

3. Upload invoice images through the web interface using either:
    - File upload button
    - Folder upload button
    - Drag and drop

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
- EasyOCR for text recognition
- Flask for the web framework
- OpenCV for image processing

## Troubleshooting

If you encounter issues, ensure that:
- Tesseract is correctly installed and its path is configured in `config.py`.
- All required Python packages are installed.
- The invoice images are clear and readable.

## FAQ

**Q: What file formats are supported?**
A: The application supports JPG, JPEG, PNG, PDF, and ZIP files.

**Q: Can I upload multiple files at once?**
A: Yes, the application supports multiple file uploads and folder uploads.

## Areas for Improvement

1. OCR Accuracy
   - Implement pre-processing filters for better image quality
   - Add support for rotated/skewed documents
   - Improve text recognition accuracy for handwritten text

2. Performance
   - Implement batch processing for multiple files
   - Add caching mechanism for processed files
   - Optimize image processing pipeline
   - Implement parallel processing for multiple files

3. Features
   - Add support for more invoice formats
   - Implement invoice template matching
   - Add data validation and correction
   - Include export options for different formats (Excel, PDF)
   - Add user authentication system
   - Implement API endpoints for integration

4. UI/UX
   - Add progress indicators for batch processing
   - Implement preview functionality
   - Add dark mode support
   - Improve mobile responsiveness
   - Add keyboard shortcuts

5. Security
   - Implement input validation
   - Add file type verification
   - Implement rate limiting
   - Add secure file handling

## Contact

For any questions or support, please contact [mertcaliskan95@gmail.com](mailto:mertcaliskan95@gmail.com).

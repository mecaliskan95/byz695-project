# Invoice Scanner

A powerful OCR-based tool for extracting data from Turkish invoices with support for multiple file formats and bilingual interface.

## 🚀 Key Features

- **Advanced OCR Processing**
  - Multi-language support (Turkish/English)
  - CUDA-accelerated processing
  - Intelligent text correction
  - Fuzzy matching for tax office validation

- **User Interface**
  - Drag-and-drop file upload
  - Folder upload support
  - Bilingual interface (EN/TR)
  - Mobile-responsive design
  - Real-time processing status

- **Data Extraction**
  - Invoice date and time
  - Tax office details
  - Cost breakdown
  - Payment methods
  - Product listings
  - VAT calculations

- **Export Options**
  - CSV export with full details
  - Raw text extraction
  - Structured data format

## 🔧 System Requirements

- Python 3.8+
- 4GB RAM minimum
- CUDA-compatible GPU (optional, for faster processing)
- Tesseract OCR
- Turkish and English language data for Tesseract and EasyOCR

## 📦 Quick Start

1. **Clone & Setup**
    ```sh
    git clone https://github.com/yourusername/byz695-project.git
    cd byz695-project
    ```

2. **Install Dependencies**
    ```sh
    pip install -r requirements.txt
    ```

3. **Verify Installation**
    - Ensure Tesseract is installed in one of these locations:
    ```python
    c:\Program Files\Tesseract-OCR\tesseract.exe
    c:\Users\[username]\AppData\Local\Programs\Tesseract-OCR\tesseract.exe
    ```

## ⚙️ Configuration

1. **Verify Tesseract Installation**
    ```sh
    tesseract --version
    ```

2. **Check Language Data**
    ```sh
    tesseract --list-langs
    ```
   Ensure 'eng' and 'tur' are listed.

3. **Test CUDA (Optional)
    ```python
    import torch
    print(torch.cuda.is_available())
    ```

## 🚀 Usage

1. **Start the Application**
    ```sh
    python app.py
    ```

2. **Access the Web Interface**
    ```
    http://localhost:5000
    ```

3. **Upload Invoices**
    - Use the file upload button
    - Use the folder upload button
    - Drag and drop files

## 📂 Project Structure

```
byz695-project/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── image_processing.py    # Image processing utilities
├── text_extraction.py     # Text extraction logic
├── requirements.txt       # Python dependencies
├── vergidaireleri.txt     # List of valid tax offices
└── templates/
    └── index.html         # Web interface template
```

## 📝 Text Extraction Details

The application extracts the following information from invoices:

- Date (DD/MM/YYYY format)
- Time (HH:MM format)
- Tax office name (validated against vergidaireleri.txt)
- Tax office number (10-digit format)
- Total cost
- VAT amount
- Payment method

## 🙏 Acknowledgments

- Tesseract OCR for text recognition
- EasyOCR for text recognition
- Flask for the web framework
- OpenCV for image processing

## 🛠️ Troubleshooting

If you encounter issues, ensure that:
- Tesseract is correctly installed and its path is configured in `config.py`.
- All required Python packages are installed.
- The invoice images are clear and readable.

## ❓ FAQ

**Q: What file formats are supported?**
A: The application supports JPG, JPEG, PNG, PDF, and ZIP files.

**Q: Can I upload multiple files at once?**
A: Yes, the application supports multiple file uploads and folder uploads.

## 🚀 Areas for Improvement

1. **OCR Accuracy**
   - Implement pre-processing filters for better image quality
   - Add support for rotated/skewed documents
   - Improve text recognition accuracy for handwritten text

2. **Performance**
   - Implement batch processing for multiple files
   - Add caching mechanism for processed files
   - Optimize image processing pipeline
   - Implement parallel processing for multiple files

3. **Features**
   - Add support for more invoice formats
   - Implement invoice template matching
   - Add data validation and correction
   - Include export options for different formats (Excel, PDF)
   - Add user authentication system
   - Implement API endpoints for integration

4. **UI/UX**
   - Add progress indicators for batch processing
   - Implement preview functionality
   - Add dark mode support
   - Improve mobile responsiveness
   - Add keyboard shortcuts

5. **Security**
   - Implement input validation
   - Add file type verification
   - Implement rate limiting
   - Add secure file handling

## 📧 Contact

For any questions or support, please contact [mertcaliskan95@gmail.com](mailto:mertcaliskan95@gmail.com).

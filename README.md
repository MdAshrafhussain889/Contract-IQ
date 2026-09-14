# Document to Markdown Converter API

A FastAPI-based REST API that converts various document formats (PDF, scanned PDF, DOCX, DOC) into Markdown files.

## Features

✅ **Multiple Format Support**
- PDF files (text-based)
- Scanned PDFs (with OCR using Tesseract)
- DOCX (Word documents)
- DOC (older Word format)

✅ **Smart Processing**
- Automatic detection of scanned vs. text-based PDFs
- OCR support for scanned documents
- Markdown formatting preservation
- Table extraction from documents

✅ **File Management**
- Temporary local storage in system temp directory
- Automatic cleanup of source files
- Persistent markdown output
- File listing and cleanup endpoints

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR (for scanned PDF support)

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### Setup Python Environment

```bash
# Clone or navigate to the project directory
cd contractiq

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the API

```bash
python main.py
```

The API will start on `http://localhost:8000`

### API Documentation

Interactive API docs available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Convert Document (Main Endpoint)

**POST** `/convert`

Upload a document and convert it to Markdown.

**Request:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -F "file=@your_document.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "Document converted successfully",
  "original_file": "your_document.pdf",
  "markdown_file_path": "/var/folders/xx/document_uploads/your_document_extracted.md",
  "markdown_filename": "your_document_extracted.md",
  "temp_directory": "/var/folders/xx/document_uploads",
  "file_size_bytes": 15234,
  "conversion_status": "completed"
}
```

**Supported Files:**
- `.pdf` - PDF documents (text and scanned)
- `.docx` - Word documents
- `.doc` - Older Word format

**Maximum File Size:** 50 MB

### 2. Health Check

**GET** `/health`

Check API status and temp directory location.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "temp_dir": "/var/folders/xx/document_uploads"
}
```

### 3. List Converted Files

**GET** `/files`

List all markdown files in the temporary directory.

```bash
curl http://localhost:8000/files
```

**Response:**
```json
{
  "success": true,
  "total_files": 3,
  "temp_directory": "/var/folders/xx/document_uploads",
  "files": [
    {
      "filename": "document1_extracted.md",
      "path": "/var/folders/xx/document_uploads/document1_extracted.md",
      "size_bytes": 12456,
      "created": 1694529201.0
    }
  ]
}
```

### 4. Cleanup Temporary Files

**DELETE** `/cleanup`

Delete all files in the temporary directory.

```bash
curl -X DELETE http://localhost:8000/cleanup
```

**Response:**
```json
{
  "success": true,
  "message": "Cleaned up 3 files",
  "temp_directory": "/var/folders/xx/document_uploads"
}
```

### 5. Health Status

**GET** `/`

Root endpoint with API information.

```bash
curl http://localhost:8000/
```

## Usage Examples

### Python Example

```python
import requests

# Upload and convert a document
files = {'file': open('my_document.pdf', 'rb')}
response = requests.post('http://localhost:8000/convert', files=files)

if response.status_code == 200:
    result = response.json()
    print(f"Markdown saved to: {result['markdown_file_path']}")
    print(f"File size: {result['file_size_bytes']} bytes")
else:
    print(f"Error: {response.json()['detail']}")
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function convertDocument(filePath) {
  const formData = new FormData();
  formData.append('file', fs.createReadStream(filePath));

  try {
    const response = await axios.post(
      'http://localhost:8000/convert',
      formData,
      { headers: formData.getHeaders() }
    );
    console.log('Conversion successful:', response.data);
  } catch (error) {
    console.error('Error:', error.response.data);
  }
}

convertDocument('my_document.pdf');
```

### cURL Example

```bash
# Upload a PDF
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -F "file=@contract.pdf"

# List converted files
curl http://localhost:8000/files

# Cleanup temp directory
curl -X DELETE http://localhost:8000/cleanup
```

## File Structure

```
contractiq/
├── main.py                    # FastAPI application
├── document_converter.py      # Document conversion logic
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Temporary Directory

By default, files are stored in the system's temporary directory under `document_uploads/`:

**macOS/Linux:** `/var/folders/xx/document_uploads/` or `/tmp/document_uploads/`
**Windows:** `C:\Users\YourUser\AppData\Local\Temp\document_uploads\`

This location is returned in all API responses.

## Error Handling

### Common Errors

| Status | Error | Solution |
|--------|-------|----------|
| 400 | Unsupported file format | Use .pdf, .docx, or .doc files |
| 413 | File too large | Maximum 50 MB file size |
| 500 | Tesseract not installed | Run `brew install tesseract` (macOS) |
| 500 | Document appears empty | Ensure document is not corrupted |

## Conversion Details

### PDF Processing
1. First attempts to extract text using `pdfplumber`
2. If no text found, assumes scanned PDF and uses OCR (Tesseract)
3. Outputs markdown with page separators (`---`)

### DOCX/DOC Processing
1. Extracts paragraphs with style preservation
2. Converts headings to markdown headers
3. Extracts tables as markdown tables
4. Maintains document structure

### Scanned PDF Processing (OCR)
- Uses Tesseract for optical character recognition
- Processes at 300 DPI for better accuracy
- Handles multi-page documents

## Performance Notes

- **Text PDFs:** Fast (< 1 second)
- **Scanned PDFs:** Slower (depends on page count and DPI, ~5-10 seconds per page)
- **DOCX/DOC:** Very fast (< 1 second)

## Logging

The API logs all operations. Check console output for:
- File upload details
- Conversion progress
- Error messages
- Cleanup operations

## Dependencies

- **fastapi** - Modern Python web framework
- **uvicorn** - ASGI server
- **python-multipart** - File upload support
- **python-docx** - DOCX file handling
- **PyPDF2** - PDF reading
- **pdfplumber** - Advanced PDF text extraction
- **pytesseract** - OCR (Tesseract Python wrapper)
- **pdf2image** - Convert PDF pages to images for OCR
- **Pillow** - Image processing

## Troubleshooting

### Tesseract Not Found Error
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```
**Solution:** Install Tesseract following the platform-specific instructions above.

### PDF Extraction Fails
- Ensure PDF is not corrupted
- Try opening the PDF in a PDF reader first
- Check file size (< 50 MB)

### DOCX Conversion Issues
- Ensure file is valid DOCX (ZIP format)
- Some encrypted documents may fail
- Corrupted files will not be processed

## Future Enhancements

- [ ] Support for additional formats (PPTX, TXT, HTML)
- [ ] Batch upload capability
- [ ] Image extraction from documents
- [ ] Webhook support for async conversions
- [ ] Database storage instead of temp files
- [ ] Custom markdown formatting options

## License

MIT License

## Support

For issues or questions, check:
1. API logs for error messages
2. Tesseract installation status
3. File format and size
4. System temporary directory permissions

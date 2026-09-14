# Quick Start Guide

Get the Document to Markdown API running in 5 minutes.

## 1️⃣ Install Dependencies

### macOS

```bash
# Install Python 3.8+ (if not already installed)
brew install python3

# Install Tesseract for OCR support (required for scanned PDFs)
brew install tesseract
```

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install python3 python3-pip tesseract-ocr
```

### Windows

1. Install Python: https://www.python.org/downloads/
2. Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki

## 2️⃣ Setup Virtual Environment

```bash
cd /Users/mac/Downloads/contractiq

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

## 3️⃣ Start the API Server

```bash
python main.py
```

You should see:
```
Starting Document to Markdown Converter API...
Temporary directory: /tmp/document_uploads
Access the API at: http://localhost:8000
API docs available at: http://localhost:8000/docs
INFO:     Started server process [12345]
```

## 4️⃣ Convert Your First Document

Open a new terminal (keep the API server running):

```bash
# Convert a PDF to Markdown
curl -X POST "http://localhost:8000/convert" \
  -F "file=@/path/to/your/document.pdf"
```

**Success response:**
```json
{
  "success": true,
  "message": "Document converted successfully",
  "markdown_filename": "document_extracted.md",
  "markdown_file_path": "/tmp/document_uploads/document_extracted.md",
  "file_size_bytes": 12345
}
```

## 5️⃣ Access Interactive API Documentation

Open your browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Try the `/convert` endpoint directly in the browser UI!

---

## 📋 Supported File Formats

- ✅ **PDF** (.pdf) - Text-based and scanned
- ✅ **Word Documents** (.docx)
- ✅ **Older Word Format** (.doc)

## 🔑 Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/convert` | Upload and convert document |
| GET | `/files` | List all converted markdown files |
| GET | `/health` | Check API status |
| DELETE | `/cleanup` | Delete all temporary files |

## 📂 File Locations

- **API runs at:** `http://localhost:8000`
- **Converted files stored in:** `/tmp/document_uploads/` (or system temp directory)
- **File naming:** `original_filename_extracted.md`

## 🚀 Python Example

```python
import requests

# Convert a document
files = {'file': open('contract.pdf', 'rb')}
response = requests.post('http://localhost:8000/convert', files=files)

if response.status_code == 200:
    result = response.json()
    print(f"✓ Success! Markdown at: {result['markdown_file_path']}")
else:
    print(f"✗ Error: {response.json()['detail']}")
```

## 📝 BASH Example

```bash
# Convert PDF
curl -X POST "http://localhost:8000/convert" \
  -F "file=@contract.pdf"

# List converted files
curl http://localhost:8000/files

# Cleanup temporary files
curl -X DELETE http://localhost:8000/cleanup
```

## 🧪 Run Automated Tests

```bash
# In another terminal while API is running:
python test_api.py
```

This runs all API endpoints through automated tests.

## ⚙️ Troubleshooting

### "Connection refused" error
- Make sure the API is running: `python main.py`
- Check if port 8000 is available: `lsof -i :8000`

### "Tesseract not found" error
- Install Tesseract:
  - macOS: `brew install tesseract`
  - Linux: `sudo apt-get install tesseract-ocr`

### File upload fails
- Check file format (must be .pdf, .docx, or .doc)
- Check file size (max 50MB)
- Check file isn't corrupted

### Scanned PDF conversion is slow
- OCR processing takes time (5-10 seconds per page)
- This is normal behavior for scanned documents

## 📚 More Information

- **Full Documentation:** See `README.md`
- **Advanced Examples:** See `EXAMPLES.md`
- **API Tests:** See `test_api.py`

## 🎯 Common Tasks

### Convert a single file
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@document.pdf" | jq '.markdown_file_path'
```

### Batch convert all PDFs in a folder
```bash
for file in *.pdf; do
  echo "Converting $file..."
  curl -X POST "http://localhost:8000/convert" -F "file=@$file"
done
```

### Download converted file (in Python)
```python
import requests
import shutil

response = requests.post(
    'http://localhost:8000/convert',
    files={'file': open('doc.pdf', 'rb')}
)

if response.status_code == 200:
    md_path = response.json()['markdown_file_path']
    shutil.copy(md_path, './my_markdown.md')
```

---

## 🛑 Stop the API

Press `Ctrl+C` in the terminal running `python main.py`

## 🔄 Next Steps

1. ✅ Read through `EXAMPLES.md` for more use cases
2. ✅ Try the interactive API docs at `/docs`
3. ✅ Integrate with your application
4. ✅ Set up batch processing for multiple files

---

Happy converting! 🎉

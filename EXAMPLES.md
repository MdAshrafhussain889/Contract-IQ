# API Usage Examples

Complete examples for using the Document to Markdown Converter API.

## Quick Start

### 1. Start the Server

```bash
python main.py
```

You should see:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete [uvicorn]
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. Convert a Document (in another terminal)

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@/path/to/your/document.pdf"
```

---

## Detailed Examples

### Convert a PDF Document

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "accept: application/json" \
  -F "file=@contract.pdf"
```

**Response:**
```json
{
  "success": true,
  "message": "Document converted successfully",
  "original_file": "contract.pdf",
  "markdown_file_path": "/var/folders/xx/document_uploads/contract_extracted.md",
  "markdown_filename": "contract_extracted.md",
  "temp_directory": "/var/folders/xx/document_uploads",
  "file_size_bytes": 45230,
  "conversion_status": "completed"
}
```

### Convert a Word Document

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@report.docx"
```

### Convert a Scanned PDF (with OCR)

```bash
# Scanned PDFs are automatically detected and processed with OCR
curl -X POST "http://localhost:8000/convert" \
  -F "file=@scanned_invoice.pdf"
```

### Health Check

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

### List All Converted Files

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
      "filename": "contract_extracted.md",
      "path": "/var/folders/xx/document_uploads/contract_extracted.md",
      "size_bytes": 45230,
      "created": 1694529201.0
    },
    {
      "filename": "report_extracted.md",
      "path": "/var/folders/xx/document_uploads/report_extracted.md",
      "size_bytes": 12456,
      "created": 1694529215.0
    }
  ]
}
```

### Cleanup Temporary Files

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

---

## Python Examples

### Basic File Upload

```python
import requests

# Upload and convert
files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:8000/convert', files=files)

if response.status_code == 200:
    result = response.json()
    print(f"✓ Conversion successful!")
    print(f"Markdown file: {result['markdown_filename']}")
    print(f"File path: {result['markdown_file_path']}")
else:
    print(f"✗ Error: {response.json()['detail']}")
```

### Batch Processing Multiple Files

```python
import requests
from pathlib import Path

# Convert all PDFs in a folder
pdf_folder = Path('./documents')
for pdf_file in pdf_folder.glob('*.pdf'):
    print(f"Processing {pdf_file.name}...")

    with open(pdf_file, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/convert',
            files={'file': f}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"  ✓ Converted to {result['markdown_filename']}")
        else:
            print(f"  ✗ Failed: {response.json()['detail']}")
```

### Save Converted Markdown Locally

```python
import requests
from pathlib import Path

def convert_and_save(document_path, output_dir='./converted'):
    """Convert document and save markdown locally."""

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    with open(document_path, 'rb') as f:
        response = requests.post(
            'http://localhost:8000/convert',
            files={'file': f}
        )

    if response.status_code == 200:
        result = response.json()
        markdown_path = result['markdown_file_path']

        # Copy to output directory
        import shutil
        local_path = output_dir / result['markdown_filename']
        shutil.copy(markdown_path, local_path)

        print(f"✓ Saved to {local_path}")
        return local_path
    else:
        raise Exception(response.json()['detail'])

# Usage
output = convert_and_save('contract.pdf', './my_markdowns')
```

### Error Handling

```python
import requests

def safe_convert(file_path):
    """Convert with proper error handling."""

    try:
        with open(file_path, 'rb') as f:
            response = requests.post(
                'http://localhost:8000/convert',
                files={'file': f},
                timeout=30
            )

        if response.status_code == 400:
            error = response.json()['detail']
            print(f"❌ Invalid file: {error}")
            return None

        elif response.status_code == 413:
            print(f"❌ File too large (max 50MB)")
            return None

        elif response.status_code == 500:
            error = response.json()['detail']
            print(f"❌ Server error: {error}")
            print("   Note: Tesseract may need to be installed for OCR")
            return None

        elif response.status_code == 200:
            print(f"✓ Conversion successful!")
            return response.json()['markdown_file_path']

    except requests.exceptions.Timeout:
        print("❌ Request timed out (file too large or API issue)")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

    return None
```

---

## JavaScript/Node.js Examples

### Basic File Upload

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

    console.log('✓ Conversion successful!');
    console.log(`Markdown file: ${response.data.markdown_filename}`);
    console.log(`File path: ${response.data.markdown_file_path}`);

  } catch (error) {
    if (error.response) {
      console.error(`✗ Error: ${error.response.data.detail}`);
    } else {
      console.error(`✗ Error: ${error.message}`);
    }
  }
}

convertDocument('document.pdf');
```

### Fetch API (Browser/Node.js)

```javascript
async function convertDocumentFetch(file) {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('http://localhost:8000/convert', {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✓ Conversion successful!');
      console.log(data);
    } else {
      const error = await response.json();
      console.error(`✗ Error: ${error.detail}`);
    }
  } catch (error) {
    console.error(`✗ Error: ${error.message}`);
  }
}

// Usage with file input
document.getElementById('fileInput').addEventListener('change', (e) => {
  convertDocumentFetch(e.target.files[0]);
});
```

### List and Download Files

```javascript
async function listConvertedFiles() {
  try {
    const response = await fetch('http://localhost:8000/files');
    const data = await response.json();

    console.log(`Total files: ${data.total_files}`);
    console.log(`Directory: ${data.temp_directory}`);

    data.files.forEach(file => {
      console.log(`- ${file.filename} (${file.size_bytes} bytes)`);
    });
  } catch (error) {
    console.error(`Error: ${error.message}`);
  }
}

listConvertedFiles();
```

---

## BASH Script Examples

### Convert All PDFs in Directory

```bash
#!/bin/bash

UPLOAD_DIR="./documents"
API_URL="http://localhost:8000"

echo "Converting all PDFs..."

for pdf_file in "$UPLOAD_DIR"/*.pdf; do
    echo "Processing: $(basename "$pdf_file")"

    response=$(curl -s -X POST "$API_URL/convert" \
        -F "file=@$pdf_file")

    markdown_file=$(echo "$response" | grep -o '"markdown_filename":"[^"]*' | cut -d'"' -f4)
    echo "✓ Converted to: $markdown_file"
done

echo "Done!"
```

### Monitor Conversions

```bash
#!/bin/bash

API_URL="http://localhost:8000"

watch_conversions() {
    while true; do
        echo "=== Converted Files ==="
        curl -s "$API_URL/files" | jq '.files[] | "\(.filename) (\(.size_bytes) bytes)"'
        echo "Refreshing in 5 seconds... (Ctrl+C to stop)"
        sleep 5
    done
}

watch_conversions
```

---

## Testing with the Included Test Script

```bash
python test_api.py
```

This runs automated tests against all API endpoints and shows results.

---

## Common Workflows

### Workflow 1: Convert PDF and Save Locally

```bash
# Convert PDF
response=$(curl -s -X POST http://localhost:8000/convert \
  -F "file=@contract.pdf")

# Extract markdown file path
md_path=$(echo "$response" | grep -o '"markdown_file_path":"[^"]*' | cut -d'"' -f4)

# Copy to local directory
cp "$md_path" "./converted_contract.md"

echo "Saved to ./converted_contract.md"
```

### Workflow 2: Batch Processing with Error Handling

```python
import requests
from pathlib import Path
import json

def batch_convert(source_dir, output_dir):
    """Batch convert all supported documents."""

    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    results = {
        'successful': [],
        'failed': []
    }

    # Support all formats
    for doc_file in list(source_path.glob('*.pdf')) + \
                    list(source_path.glob('*.docx')) + \
                    list(source_path.glob('*.doc')):

        print(f"Converting {doc_file.name}...")

        try:
            with open(doc_file, 'rb') as f:
                response = requests.post(
                    'http://localhost:8000/convert',
                    files={'file': f},
                    timeout=60
                )

            if response.status_code == 200:
                result = response.json()
                # Copy to output
                import shutil
                shutil.copy(
                    result['markdown_file_path'],
                    output_path / result['markdown_filename']
                )
                results['successful'].append(doc_file.name)
                print(f"  ✓ Success")
            else:
                results['failed'].append({
                    'file': doc_file.name,
                    'error': response.json()['detail']
                })
                print(f"  ✗ Failed: {response.json()['detail']}")

        except Exception as e:
            results['failed'].append({
                'file': doc_file.name,
                'error': str(e)
            })
            print(f"  ✗ Error: {str(e)}")

    # Save results
    with open(output_path / 'conversion_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {output_path / 'conversion_results.json'}")
    return results

# Usage
results = batch_convert('./documents', './converted')
print(f"Successful: {len(results['successful'])}")
print(f"Failed: {len(results['failed'])}")
```

---

## Performance Tips

1. **For Scanned PDFs:** Files with many pages may take longer due to OCR
2. **Batch Processing:** Avoid sending too many simultaneous requests
3. **File Size:** Keep files under 50MB for optimal performance
4. **Cleanup:** Regularly run `DELETE /cleanup` to free disk space

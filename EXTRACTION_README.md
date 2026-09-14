# Contract Field Extraction API

Extract 12 predefined contract fields from Markdown documents using Claude AI and store results in SQLite.

## 🎯 Features

✅ **Automated Field Extraction** - Extract 12 contract fields using Claude AI  
✅ **LLM-Powered** - Uses Claude Sonnet for accurate data extraction  
✅ **Structured Output** - Returns validated Pydantic/SQLModel objects  
✅ **Database Storage** - Stores all extractions in SQLite  
✅ **Type Validation** - Automatic type conversion and validation  
✅ **Error Handling** - Comprehensive error messages and logging  

---

## 📋 Extracted Fields

1. **subject_to_lease** - Whether property is subject to lease/tenancy
2. **date_of_tenancy** - Date tenancy begins (YYYY-MM-DD)
3. **contract_price** - Agreed purchase price (numeric)
4. **deposit_amount** - Required deposit (numeric)
5. **deposit_due_date** - Deposit payment due date (YYYY-MM-DD)
6. **subject_to_finance** - Finance approval condition (boolean)
7. **settlement_date** - Settlement/completion date
8. **gst_clause** - GST clause details
9. **terms_contract** - Key contractual terms
10. **default_provisions** - Default/breach provisions
11. **due_date_extension** - Extension provisions
12. **special_conditions** - Special/unique clauses

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with API key
cp .env.example .env
# Edit .env and add your Anthropic API key
export ANTHROPIC_API_KEY="your-api-key"
```

### 2. Start the API

```bash
python main.py
```

Server starts at: `http://localhost:8000`

### 3. Extract Contract Fields

**Option A: Using cURL**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md"
  }'
```

**Option B: Using Python**
```python
import requests

response = requests.post(
    'http://localhost:8000/extract',
    json={
        "markdown_file_path": "/path/to/contract_extracted.md"
    }
)

result = response.json()
print(f"✅ Extraction ID: {result['extraction_id']}")
print(f"Contract Price: ${result['extracted_fields']['contract_price']}")
```

**Option C: Using Swagger UI**
1. Open http://localhost:8000/docs
2. Click on "POST /extract"
3. Click "Try it out"
4. Fill in the markdown file path
5. Click "Execute"

---

## 📊 Database Schema

**Table:** `contract_extracts`

```sql
CREATE TABLE contract_extracts (
    id INTEGER PRIMARY KEY,
    subject_to_lease TEXT,
    date_of_tenancy DATE,
    contract_price DECIMAL,
    deposit_amount DECIMAL,
    deposit_due_date DATE,
    subject_to_finance BOOLEAN,
    settlement_date TEXT,
    gst_clause TEXT,
    terms_contract TEXT,
    default_provisions TEXT,
    due_date_extension TEXT,
    special_conditions TEXT,
    markdown_filename TEXT,
    folder_path TEXT,
    extraction_timestamp DATETIME
);
```

**Database Location:** `/Users/mac/Downloads/contractiq/data/contracts.db`

---

## 🔗 API Endpoints

### Extract Contract Fields
**POST** `/extract`

Request:
```json
{
  "markdown_file_path": "/path/to/markdown/file.md"
}
```

Response:
```json
{
  "success": true,
  "message": "Contract fields extracted successfully",
  "extraction_id": 1,
  "extracted_fields": {
    "id": 1,
    "subject_to_lease": "Yes — tenanted",
    "date_of_tenancy": "2026-11-14",
    "contract_price": 1285000,
    "deposit_amount": 128500,
    ...
  },
  "timestamp": "2026-09-12T19:30:00"
}
```

---

### List All Extractions
**GET** `/extractions`

Response:
```json
{
  "success": true,
  "total_extractions": 5,
  "extractions": [
    {
      "id": 1,
      "markdown_filename": "contract_extracted.md",
      "folder_path": "/path/to/folder",
      "extraction_timestamp": "2026-09-12T19:30:00",
      "subject_to_lease": "Yes — tenanted",
      "contract_price": 1285000,
      ...
    }
  ]
}
```

---

### Get Specific Extraction
**GET** `/extractions/{extraction_id}`

Response:
```json
{
  "id": 1,
  "markdown_filename": "contract_extracted.md",
  "folder_path": "/path/to/folder",
  "extraction_timestamp": "2026-09-12T19:30:00",
  "subject_to_lease": "Yes — tenanted",
  "date_of_tenancy": "2026-11-14",
  "contract_price": 1285000,
  ...
}
```

---

## 🛠️ Project Structure

```
contractiq/
├── models/
│   ├── __init__.py
│   └── contract_extract.py     # SQLModel schema
├── services/
│   ├── __init__.py
│   └── contract_extractor.py   # Claude extraction service
├── data/
│   └── contracts.db            # SQLite database
├── main.py                      # FastAPI application
├── db.py                        # Database configuration
├── prompts.py                   # Extraction prompt
├── requirements.txt             # Dependencies
├── .env                         # Environment variables
├── .env.example                 # Example environment file
└── EXTRACTION_README.md         # This file
```

---

## 📝 Extraction Process

```
Markdown File (contract_extracted.md)
         ↓
   Read File Content
         ↓
Build Extraction Prompt
(with extraction rules and document context)
         ↓
Send to Claude AI
         ↓
Structured Output (JSON)
         ↓
Pydantic Validation
(type conversion, null handling)
         ↓
SQLModel Database Record
         ↓
SQLite Storage
         ↓
Return Extraction ID & Data
```

---

## 🔒 Extraction Rules

The LLM follows strict extraction rules:

1. ✅ Extract only explicitly stated information
2. ✅ Do not infer, assume, or calculate values
3. ✅ Preserve contractual meaning
4. ✅ Return `null` for missing fields
5. ✅ Normalize dates to YYYY-MM-DD format
6. ✅ Extract monetary values as numbers only
7. ✅ Return boolean fields as true/false/null
8. ✅ Extract clause text faithfully

---

## 🎯 Usage Examples

### Example 1: Extract and Display Results

```python
import requests
import json

response = requests.post(
    'http://localhost:8000/extract',
    json={
        "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md"
    }
)

if response.status_code == 200:
    result = response.json()
    fields = result['extracted_fields']
    
    print("📋 Contract Extraction Results")
    print("=" * 50)
    print(f"Subject to Lease: {fields['subject_to_lease']}")
    print(f"Contract Price: ${fields['contract_price']:,.2f}")
    print(f"Deposit Amount: ${fields['deposit_amount']:,.2f}")
    print(f"Settlement Date: {fields['settlement_date']}")
    print(f"Subject to Finance: {fields['subject_to_finance']}")
else:
    print(f"Error: {response.json()['detail']}")
```

### Example 2: Bulk Extraction

```python
import requests
from pathlib import Path

# Find all contract markdown files
contract_dir = Path('/Users/mac/Downloads/contractiq/tempfolder')

for folder in contract_dir.glob('*/'):
    markdown_file = folder / f"{folder.name}_extracted.md"
    
    if markdown_file.exists():
        print(f"Extracting: {markdown_file.name}...")
        
        response = requests.post(
            'http://localhost:8000/extract',
            json={"markdown_file_path": str(markdown_file)}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Extraction ID: {result['extraction_id']}")
        else:
            print(f"  ❌ Error: {response.json()['detail']}")
```

### Example 3: Query Extracted Data

```python
import requests

# Get all extractions
response = requests.get('http://localhost:8000/extractions')
extractions = response.json()

print(f"Total Extractions: {extractions['total_extractions']}")

for extraction in extractions['extractions']:
    print(f"\nID: {extraction['id']}")
    print(f"File: {extraction['markdown_filename']}")
    print(f"Price: ${extraction['contract_price']:,.2f}")
    print(f"Finance Required: {extraction['subject_to_finance']}")
```

---

## 🐛 Troubleshooting

### Error: `ANTHROPIC_API_KEY environment variable not set`

**Solution:**
```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .env file
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

### Error: `File not found`

**Solution:**
- Verify the markdown file path is correct
- Ensure the file exists in the tempfolder
- Use absolute paths in requests

### Error: `Validation error`

**Solution:**
- The LLM may not have found certain fields (returns null)
- This is expected behavior - not all contracts have all fields
- Check extracted_fields in response for what was found

### Error: `Database locked`

**Solution:**
- Close other connections to the SQLite database
- SQLite has limited concurrent write support
- For multiple concurrent requests, consider PostgreSQL

---

## 📊 Monitoring Extractions

### View Database Content (Command Line)

```bash
# List all extractions
sqlite3 data/contracts.db "SELECT id, markdown_filename, contract_price FROM contract_extracts;"

# View specific extraction
sqlite3 data/contracts.db "SELECT * FROM contract_extracts WHERE id=1;"

# Count total extractions
sqlite3 data/contracts.db "SELECT COUNT(*) as total FROM contract_extracts;"
```

### View via API

```bash
# List all with formatting
curl http://localhost:8000/extractions | jq '.extractions[] | {id, markdown_filename, contract_price}'

# Get specific extraction
curl http://localhost:8000/extractions/1 | jq '.contract_price'
```

---

## 🔄 Workflow: Document → Extraction → Database

1. **Upload Document**
   - POST /convert
   - Creates: `/tempfolder/contract/contract.pdf` + `contract_extracted.md`

2. **Extract Fields**
   - POST /extract with markdown file path
   - Claude AI extracts 12 fields
   - Validates data types
   - Stores in SQLite

3. **Query Results**
   - GET /extractions
   - GET /extractions/{id}
   - Access extracted data

---

## 📚 API Documentation

Complete interactive documentation available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Both include:
- ✅ Detailed endpoint descriptions
- ✅ Sample requests and responses
- ✅ "Try it out" functionality
- ✅ Schema documentation
- ✅ Error response examples

---

## 📦 Dependencies

- `anthropic` - Claude API client
- `sqlmodel` - SQL database ORM
- `fastapi` - Web framework
- `pydantic` - Data validation
- `python-dotenv` - Environment variables

---

## 🎓 Learning Resources

- [Claude API Documentation](https://docs.anthropic.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API logs for detailed errors
3. Verify .env configuration
4. Check database connectivity

---

**Version:** 1.0.0  
**Last Updated:** 2026-09-12  
**Database:** SQLite

# Contract Field Extraction - Implementation Guide

Complete implementation of AI-powered contract field extraction with FastAPI, Claude AI, and SQLite.

## ✅ Implementation Complete

All components have been successfully created and integrated.

---

## 🗂️ Project Structure

```
contractiq/
├── models/
│   ├── __init__.py                 # Package initialization
│   └── contract_extract.py         # SQLModel schema (12 fields)
│
├── services/
│   ├── __init__.py                 # Package initialization
│   └── contract_extractor.py       # Claude extraction service
│
├── data/
│   └── contracts.db                # SQLite database (auto-created)
│
├── tempfolder/                     # Markdown files storage
│   └── {document_name}/
│       ├── {original_file}         # Original PDF/DOCX/DOC
│       └── {document_name}_extracted.md  # Converted markdown
│
├── main.py                         # FastAPI application (updated)
├── db.py                           # Database setup and config
├── prompts.py                      # Extraction prompt template
├── document_converter.py           # PDF/DOCX → Markdown converter
├── requirements.txt                # All dependencies
├── .env                            # Environment variables
├── .env.example                    # Example env file
├── README.md                       # Main documentation
├── QUICKSTART.md                   # Quick start guide
├── EXAMPLES.md                     # Usage examples
├── EXTRACTION_README.md            # Extraction feature docs
└── IMPLEMENTATION_GUIDE.md         # This file
```

---

## 🔧 What Was Created

### 1. **SQLModel Schema** (`models/contract_extract.py`)
- Defines database table `contract_extracts`
- 12 contract fields + metadata
- Automatic Pydantic validation
- Type hints for all fields

### 2. **Extraction Service** (`services/contract_extractor.py`)
- Reads markdown files from tempfolder
- Sends content to Claude API
- Extracts 12 predefined fields
- Validates output against schema
- Handles errors gracefully

### 3. **Database Configuration** (`db.py`)
- SQLite setup with SQLModel
- Auto-creates tables
- Session management
- Location: `/Users/mac/Downloads/contractiq/data/contracts.db`

### 4. **Prompt Template** (`prompts.py`)
- Extraction instructions
- Field definitions
- Output format specifications
- Builds complete prompt with document content

### 5. **API Endpoints** (in `main.py`)
- `POST /extract` - Extract contract fields
- `GET /extractions` - List all extractions
- `GET /extractions/{id}` - Get specific extraction
- Complete Swagger documentation

### 6. **Environment Setup**
- `.env` file for API keys
- `.env.example` as template
- Automatic environment loading

---

## 📋 12 Extracted Fields

| # | Field | Type | Example |
|---|-------|------|---------|
| 1 | subject_to_lease | string | "Yes — tenanted" |
| 2 | date_of_tenancy | string | "2026-11-14" |
| 3 | contract_price | float | 1285000 |
| 4 | deposit_amount | float | 128500 |
| 5 | deposit_due_date | string | "2026-09-13" |
| 6 | subject_to_finance | boolean | true |
| 7 | settlement_date | string | "30 days from signing" |
| 8 | gst_clause | string | "Price is GST inclusive" |
| 9 | terms_contract | string | "Standard terms apply" |
| 10 | default_provisions | string | "Interest 12% p.a. on default" |
| 11 | due_date_extension | string | null |
| 12 | special_conditions | string | "14 identified" |

---

## 🚀 Quick Start

### 1. Set Up Environment

```bash
cd /Users/mac/Downloads/contractiq

# Create .env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start the API

```bash
python main.py
```

Output:
```
🚀 Starting Document to Markdown Converter API...
📁 Temporary directory: /Users/mac/Downloads/contractiq/tempfolder
💾 Initializing database...
✅ Database initialized at: /Users/mac/Downloads/contractiq/data/contracts.db
🌐 Access the API at: http://localhost:8000
📚 API docs available at: http://localhost:8000/docs
```

### 3. Test Extraction

**Convert a document to markdown first:**
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@contract.pdf"
```

**Then extract fields:**
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md"
  }'
```

---

## 📡 API Endpoints

### POST /extract - Extract Contract Fields

**Request:**
```json
{
  "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md"
}
```

**Response (Success - 200):**
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
    "deposit_due_date": "2026-09-13",
    "subject_to_finance": true,
    "settlement_date": "30 days from signing",
    "gst_clause": "Price is GST inclusive",
    "terms_contract": "Standard terms apply",
    "default_provisions": "Interest 12% p.a. on default",
    "due_date_extension": null,
    "special_conditions": "14 identified",
    "markdown_filename": "contract_extracted.md",
    "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/contract",
    "extraction_timestamp": "2026-09-12T20:00:00"
  },
  "timestamp": "2026-09-12T20:00:00"
}
```

**Error Response (400):**
```json
{
  "detail": "File not found: /path/to/nonexistent/file.md"
}
```

---

### GET /extractions - List All Extractions

**Request:**
```bash
curl http://localhost:8000/extractions
```

**Response:**
```json
{
  "success": true,
  "total_extractions": 5,
  "extractions": [
    {
      "id": 1,
      "subject_to_lease": "Yes — tenanted",
      "date_of_tenancy": "2026-11-14",
      "contract_price": 1285000,
      ...
    }
  ]
}
```

---

### GET /extractions/{id} - Get Specific Extraction

**Request:**
```bash
curl http://localhost:8000/extractions/1
```

**Response:**
```json
{
  "id": 1,
  "subject_to_lease": "Yes — tenanted",
  "date_of_tenancy": "2026-11-14",
  "contract_price": 1285000,
  ...
}
```

---

## 💾 Database Details

### Location
```
/Users/mac/Downloads/contractiq/data/contracts.db
```

### Table: contract_extracts
```sql
CREATE TABLE contract_extracts (
    id INTEGER PRIMARY KEY,
    subject_to_lease TEXT,
    date_of_tenancy TEXT,
    contract_price FLOAT,
    deposit_amount FLOAT,
    deposit_due_date TEXT,
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

### Query Examples

```bash
# List all extractions
sqlite3 data/contracts.db "SELECT id, markdown_filename, contract_price FROM contract_extracts;"

# Get specific extraction
sqlite3 data/contracts.db "SELECT * FROM contract_extracts WHERE id=1;"

# Count extractions
sqlite3 data/contracts.db "SELECT COUNT(*) as total FROM contract_extracts;"

# Find expensive contracts
sqlite3 data/contracts.db "SELECT markdown_filename, contract_price FROM contract_extracts WHERE contract_price > 1000000;"
```

---

## 🔄 Full Workflow

### Step 1: Upload Document
```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@contract.pdf"
```

**Creates:**
- `/tempfolder/contract/contract.pdf` (original)
- `/tempfolder/contract/contract_extracted.md` (markdown)

### Step 2: Extract Fields
```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md"
  }'
```

**Result:**
- 12 fields extracted using Claude AI
- Validated against schema
- Stored in SQLite

### Step 3: Query Results
```bash
# List all extractions
curl http://localhost:8000/extractions

# Get specific extraction
curl http://localhost:8000/extractions/1
```

---

## 🛠️ Configuration

### Environment Variables (.env)
```
ANTHROPIC_API_KEY=sk-ant-...
```

Get your API key from: https://console.anthropic.com/account/keys

### Database
- Type: SQLite
- Location: `/Users/mac/Downloads/contractiq/data/contracts.db`
- Auto-created on first run

### API Server
- Host: `0.0.0.0`
- Port: `8000`
- Reload: Off (production mode)

---

## 📊 Extraction Process Flow

```
1. Upload Document
   ↓ (POST /convert)
   ├─ Original File → tempfolder/name/file.pdf
   └─ Markdown → tempfolder/name/name_extracted.md

2. Extract Fields
   ↓ (POST /extract)
   ├─ Read markdown file
   ├─ Build extraction prompt
   ├─ Send to Claude API
   └─ Get JSON response

3. Validate & Store
   ↓
   ├─ Validate with Pydantic
   ├─ Create database record
   ├─ Insert into SQLite
   └─ Return extraction ID

4. Query Results
   ↓ (GET /extractions or GET /extractions/{id})
   ├─ Fetch from database
   ├─ Convert to response model
   └─ Return to client
```

---

## 🎓 Key Implementation Details

### Pydantic Validation
- All extracted fields validated automatically
- Type conversion handled
- Null values preserved for missing fields

### Error Handling
- File not found → 400 Bad Request
- Extraction error → 500 Internal Server Error
- Database error → 500 Internal Server Error
- All errors logged to console

### Data Types
```python
subject_to_lease: Optional[str]
date_of_tenancy: Optional[str]          # YYYY-MM-DD format
contract_price: Optional[float]         # Numeric only
deposit_amount: Optional[float]         # Numeric only
deposit_due_date: Optional[str]         # YYYY-MM-DD format
subject_to_finance: Optional[bool]      # true/false/null
settlement_date: Optional[str]
gst_clause: Optional[str]
terms_contract: Optional[str]
default_provisions: Optional[str]
due_date_extension: Optional[str]
special_conditions: Optional[str]
```

---

## 📚 Swagger Documentation

Access at: **http://localhost:8000/docs**

Features:
- ✅ All endpoints documented
- ✅ Sample requests/responses
- ✅ "Try it out" functionality
- ✅ Schema documentation
- ✅ Error examples

---

## 🔍 Testing the Extraction

### Test with Sample Markdown

Create a test markdown file with contract content:

```bash
# Create test markdown
cat > /Users/mac/Downloads/contractiq/tempfolder/test/test_extracted.md << 'EOF'
# Contract Details

Subject to Lease: Yes - property is subject to existing tenancy

Date of Tenancy: 14 November 2026

Contract Price: $1,285,000

Deposit Amount: 10% deposit of $128,500

Deposit Due Date: On signing

Subject to Finance: Yes - subject to 21 day finance approval

Settlement Date: 30 days from signing date

GST Clause: Price is GST inclusive

Terms: Standard contract terms apply

Default Provisions: If party defaults, interest at 12% per annum

Special Conditions: Property has 3 special conditions affecting purchaser
EOF

# Extract fields
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/test/test_extracted.md"
  }' | jq '.'
```

---

## 🚨 Troubleshooting

### API Won't Start

**Error:** `ModuleNotFoundError: No module named 'anthropic'`

**Solution:**
```bash
source venv/bin/activate
pip install anthropic
```

### Extraction Fails

**Error:** `ANTHROPIC_API_KEY environment variable not set`

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# or add to .env file
```

### Database Issues

**Error:** `database is locked`

**Solution:**
- Close other connections to the database
- SQLite has limited concurrent write support
- For production, consider PostgreSQL

---

## 📈 Monitoring & Analytics

### View Extraction History

```bash
# All extractions
curl http://localhost:8000/extractions | jq '.total_extractions'

# Average contract price
curl http://localhost:8000/extractions | \
  jq '.extractions[].contract_price | select(. != null)' | \
  jq -s 'add / length'

# Count finance-required contracts
curl http://localhost:8000/extractions | \
  jq '[.extractions[] | select(.subject_to_finance == true)] | length'
```

---

## 🔐 Security Notes

- ✅ API keys stored in .env (not in code)
- ✅ Don't commit .env file
- ✅ Database is local (not exposed)
- ✅ All inputs validated
- ✅ Error messages don't leak sensitive data

---

## 📦 Dependencies Added

```
anthropic==0.28.0          # Claude AI API
sqlmodel==0.0.14           # SQLite ORM
python-dotenv==1.0.0       # Environment variables
```

---

## 🎯 Next Steps

1. **Get API Key**: https://console.anthropic.com/account/keys
2. **Add to .env**: `ANTHROPIC_API_KEY=sk-ant-...`
3. **Start Server**: `python main.py`
4. **Test API**: http://localhost:8000/docs
5. **Upload Document**: Use POST /convert
6. **Extract Fields**: Use POST /extract
7. **View Results**: Use GET /extractions

---

## 📞 Support

For issues:
1. Check Swagger docs: http://localhost:8000/docs
2. Review EXTRACTION_README.md
3. Check .env configuration
4. Verify markdown file path
5. Check server logs

---

## 🎉 Implementation Summary

✅ Database schema created  
✅ Extraction service implemented  
✅ API endpoints added  
✅ Swagger documentation generated  
✅ Error handling implemented  
✅ Environment configuration done  
✅ Sample payloads added  

**Status:** Ready for production use! 🚀

---

**Version:** 1.0.0  
**Date:** September 12, 2026  
**Tech Stack:** FastAPI + Claude AI + SQLite

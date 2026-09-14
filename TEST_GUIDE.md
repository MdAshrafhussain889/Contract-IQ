# Testing Guide - ContractIQ

Complete step-by-step guide to test the full document conversion and field extraction workflow.

## 🎯 Prerequisites

✅ API is running at http://localhost:8000  
✅ OpenAI API key is in `.env` file  
✅ Test PDF exists at `/Users/mac/Downloads/contractiq/test_contract.pdf`

---

## 📋 Test Data in PDF

The test PDF contains realistic contract data with all 12 fields:

```
1.  subject_to_lease          → Yes — tenanted
2.  date_of_tenancy           → 14 November 2026
3.  contract_price            → $1,285,000
4.  deposit_amount            → $128,500
5.  deposit_due_date          → On signing
6.  subject_to_finance        → Yes — 21 days
7.  settlement_date           → 30 days from signing
8.  gst_clause                → GST inclusive
9.  terms_contract            → Standard terms apply
10. default_provisions        → 12% interest p.a.
11. due_date_extension        → 14 days by mutual agreement
12. special_conditions        → 14 identified
```

Plus lots of junk content to test extraction accuracy!

---

## 🚀 Step 1: Convert PDF to Markdown

### Option A: Using Swagger UI (Recommended)

1. **Open** http://localhost:8000/docs
2. **Find** the "POST /convert" endpoint
3. **Click** "Try it out"
4. **Upload** the test PDF:
   - Click "Choose File"
   - Select: `/Users/mac/Downloads/contractiq/test_contract.pdf`
5. **Click** "Execute"

**Expected Response:**
```json
{
  "success": true,
  "message": "Document converted successfully",
  "original_file": "test_contract.pdf",
  "original_file_path": "/Users/mac/Downloads/contractiq/tempfolder/test_contract/test_contract.pdf",
  "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/test_contract/test_contract_extracted.md",
  "file_folder": "/Users/mac/Downloads/contractiq/tempfolder/test_contract",
  ...
}
```

### Option B: Using cURL

```bash
curl -X POST "http://localhost:8000/convert" \
  -F "file=@/Users/mac/Downloads/contractiq/test_contract.pdf"
```

### ✅ Step 1 Complete When:
- Response status is 200
- `markdown_file_path` is provided
- You see the file_folder in the response

**Save the markdown file path for Step 2!**

---

## 🎯 Step 2: Extract Contract Fields

### Prerequisites for Step 2:
1. Update `.env` with your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-...your-actual-key...
   ```
2. Save the markdown path from Step 1

### Option A: Using Swagger UI (Recommended)

1. **Open** http://localhost:8000/docs
2. **Find** the "POST /extract" endpoint
3. **Click** "Try it out"
4. **Enter** the markdown file path from Step 1:
   ```json
   {
     "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/test_contract/test_contract_extracted.md"
   }
   ```
5. **Click** "Execute"

**Expected Response:**
```json
{
  "success": true,
  "message": "Contract fields extracted successfully",
  "extraction_id": 1,
  "extracted_fields": {
    "id": 1,
    "subject_to_lease": "Yes — tenanted arrangement continues",
    "date_of_tenancy": "2026-11-14",
    "contract_price": 1285000,
    "deposit_amount": 128500,
    "deposit_due_date": "On signing",
    "subject_to_finance": true,
    "settlement_date": "30 days from signing",
    "gst_clause": "Price is GST inclusive",
    "terms_contract": "Standard contract terms apply",
    "default_provisions": "Interest at 12% per annum",
    "due_date_extension": "14 days by mutual agreement",
    "special_conditions": "14 identified — 3 affect purchaser",
    "markdown_filename": "test_contract_extracted.md",
    "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/test_contract",
    "extraction_timestamp": "2026-09-12T20:15:30"
  },
  "timestamp": "2026-09-12T20:15:30"
}
```

### Option B: Using cURL

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/test_contract/test_contract_extracted.md"
  }'
```

### ✅ Step 2 Complete When:
- Response status is 200
- `extraction_id` is returned (e.g., 1)
- All 12 fields are populated
- Data is stored in SQLite database

**Save the extraction_id for Step 3!**

---

## 📊 Step 3: Query Results from Database

### Option A: List All Extractions

**Swagger UI:**
1. Find "GET /extractions" endpoint
2. Click "Try it out"
3. Click "Execute"

**cURL:**
```bash
curl http://localhost:8000/extractions
```

**Expected Response:**
```json
{
  "success": true,
  "total_extractions": 1,
  "extractions": [
    {
      "id": 1,
      "subject_to_lease": "Yes — tenanted arrangement continues",
      "date_of_tenancy": "2026-11-14",
      "contract_price": 1285000,
      ...
    }
  ]
}
```

### Option B: Get Specific Extraction

**Swagger UI:**
1. Find "GET /extractions/{extraction_id}" endpoint
2. Click "Try it out"
3. Enter extraction_id: `1`
4. Click "Execute"

**cURL:**
```bash
curl http://localhost:8000/extractions/1
```

---

## 🎓 Expected Values from Test PDF

When you extract the test PDF, you should get these values:

| Field | Expected Value |
|-------|-----------------|
| subject_to_lease | Yes — tenanted |
| date_of_tenancy | 2026-11-14 |
| contract_price | 1285000 |
| deposit_amount | 128500 |
| deposit_due_date | On signing |
| subject_to_finance | true |
| settlement_date | 30 days from signing |
| gst_clause | Price is GST inclusive |
| terms_contract | Standard terms apply |
| default_provisions | Interest at 12% per annum |
| due_date_extension | 14 days by mutual agreement |
| special_conditions | 14 identified |

---

## 🐛 Troubleshooting

### Issue: "OpenAI API key not set"
**Solution:** Add your key to `.env`:
```
OPENAI_API_KEY=sk-...your-key...
```

### Issue: "File not found"
**Solution:** Make sure you're using the correct markdown path from Step 1

### Issue: Some fields are null
**This is expected!** GPT extracts only explicitly stated information. Not all fields appear clearly in every contract.

### Issue: Port 8000 already in use
**Solution:**
```bash
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9
python main.py
```

---

## 📱 Quick Test Script (Python)

```python
import requests
import json

# Step 1: Convert PDF
print("Step 1: Converting PDF to Markdown...")
with open("/Users/mac/Downloads/contractiq/test_contract.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/convert",
        files={"file": f}
    )

if response.status_code == 200:
    result = response.json()
    markdown_path = result["markdown_file_path"]
    print(f"✅ Converted to: {markdown_path}")
else:
    print(f"❌ Error: {response.json()}")
    exit(1)

# Step 2: Extract fields
print("\nStep 2: Extracting contract fields...")
response = requests.post(
    "http://localhost:8000/extract",
    json={"markdown_file_path": markdown_path}
)

if response.status_code == 200:
    result = response.json()
    extraction_id = result["extraction_id"]
    fields = result["extracted_fields"]
    
    print(f"✅ Extraction ID: {extraction_id}")
    print("\nExtracted Fields:")
    for field, value in fields.items():
        if field.startswith("_") or field in ["id", "markdown_filename", "folder_path", "extraction_timestamp"]:
            continue
        print(f"  {field}: {value}")
else:
    print(f"❌ Error: {response.json()}")
    exit(1)

# Step 3: Query results
print("\nStep 3: Querying database...")
response = requests.get("http://localhost:8000/extractions")
if response.status_code == 200:
    result = response.json()
    print(f"✅ Total extractions in database: {result['total_extractions']}")
else:
    print(f"❌ Error: {response.json()}")

print("\n✅ Full workflow completed successfully!")
```

---

## 📊 Success Indicators

✅ **Step 1 Success:**
- PDF uploads successfully
- Markdown file is created
- Both original PDF and markdown stored in folder

✅ **Step 2 Success:**
- OpenAI API returns structured JSON
- All 12 fields are extracted
- Data is stored in SQLite database
- Extraction ID is returned

✅ **Step 3 Success:**
- Can retrieve extracted data from database
- Data matches original contract
- Timestamp shows when extraction occurred

---

## 🎯 Next Steps After Testing

1. **Test with your own documents** - Upload different contract types
2. **Verify accuracy** - Check extracted values against original
3. **Monitor database** - Use SQLite to query extraction history
4. **Scale up** - Batch process multiple contracts

---

**Ready to test? Start with Step 1! 🚀**

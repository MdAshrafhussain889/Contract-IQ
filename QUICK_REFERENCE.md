# Quick Reference Card - Extraction Format

## 📋 The New Format (One Page Summary)

### Response Structure
```json
{
    "extracted_parameters": [
        {
            "parameter_name": "contract_price",
            "parameter_value": "1285000",
            "confidence_score": 98,
            "reference": {
                "page_num": 2,
                "section_number": "3.2",
                "section_title": "Purchase Price"
            }
        }
    ]
}
```

---

## 🎯 Confidence Score Reference

| Score | Level | Action |
|-------|-------|--------|
| 90-100 | Very High | ✅ Use in automation |
| 70-89 | High | ⚠️ Use with review |
| 50-69 | Medium | 🔍 Manual review needed |
| 0-49 | Low | ❌ Manual extraction |

---

## 💻 Quick Code Examples

### Python - Extract & Display
```python
import requests

resp = requests.post('http://localhost:8000/extract',
    json={"markdown_file_path": "/path/to/contract.md"})

for p in resp.json()['extracted_parameters']:
    print(f"{p['parameter_name']}: {p['parameter_value']} "
          f"({p['confidence_score']}%) - {p['reference']['section_title']}")
```

### Python - Filter High Confidence
```python
high_conf = [p for p in result['extracted_parameters'] 
             if p['confidence_score'] >= 90]
```

### Python - Export to CSV
```python
import csv
with open('results.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['param_name', 'value', 'confidence'])
    writer.writeheader()
    for p in result['extracted_parameters']:
        writer.writerow({
            'param_name': p['parameter_name'],
            'value': p['parameter_value'],
            'confidence': p['confidence_score']
        })
```

### cURL - Extract
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"markdown_file_path": "/path/to/contract.md"}' \
  | jq '.extracted_parameters[] | {parameter_name, confidence_score}'
```

### JavaScript - Extract & Filter
```javascript
const resp = await fetch('http://localhost:8000/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ markdown_file_path: '/path/to/contract.md' })
});

const data = await resp.json();
const highConf = data.extracted_parameters.filter(p => p.confidence_score >= 90);
highConf.forEach(p => console.log(`${p.parameter_name}: ${p.parameter_value}`));
```

---

## 📊 Data Model

```python
class Reference(BaseModel):
    page_num: Optional[int] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None

class ExtractedParameter(BaseModel):
    parameter_name: str
    parameter_value: Optional[str] = None
    confidence_score: int  # 0-100
    reference: Reference
```

---

## 🔑 The 12 Extracted Fields

1. **subject_to_lease** - Property lease status
2. **date_of_tenancy** - Tenancy start date
3. **contract_price** - Purchase price
4. **deposit_amount** - Deposit required
5. **deposit_due_date** - Deposit due date
6. **subject_to_finance** - Finance condition
7. **settlement_date** - Settlement date
8. **gst_clause** - GST provision
9. **terms_contract** - Contract terms
10. **default_provisions** - Default clauses
11. **due_date_extension** - Extension provisions
12. **special_conditions** - Special clauses

---

## 📁 Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| **README_EXTRACTION.md** | Master index & navigation | 5 min |
| **QUICK_START_EXTRACTION.md** | Quick examples & use cases | 10 min |
| **EXTRACTION_FORMAT_GUIDE.md** | Complete reference | 20 min |
| **MODIFICATIONS_SUMMARY.md** | Technical details | 15 min |
| **EXTRACTION_CHANGES.md** | Overview & features | 10 min |
| **test_extraction_format.py** | Working code examples | Run it |

---

## ✅ Quick Checklist

- [ ] Read README_EXTRACTION.md
- [ ] Run test_extraction_format.py
- [ ] Test API: `curl -X POST http://localhost:8000/extract ...`
- [ ] Integrate into your application
- [ ] Filter by confidence: `[p for p in params if p['confidence_score'] >= 90]`
- [ ] Monitor extraction quality

---

## 🚀 Common Tasks

### Get High-Confidence Extractions
```python
high = [p for p in params if p['confidence_score'] >= 90]
```

### Group by Confidence Level
```python
from collections import defaultdict
groups = defaultdict(list)
for p in params:
    level = 'High' if p['confidence_score'] >= 90 else 'Low'
    groups[level].append(p)
```

### Find Specific Field
```python
params_dict = {p['parameter_name']: p for p in params}
price_param = params_dict.get('contract_price')
```

### Calculate Quality Score
```python
avg_conf = sum(p['confidence_score'] for p in params) / len(params)
print(f"Extraction quality: {avg_conf:.1f}%")
```

### Track Parameter Locations
```python
for p in params:
    location = f"Page {p['reference']['page_num']}, {p['reference']['section_title']}"
    print(f"{p['parameter_name']}: {location}")
```

---

## 🔗 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/extract` | Extract fields (returns new format) |
| GET | `/extractions` | List all extractions |
| GET | `/extractions/{id}` | Get specific extraction |

---

## 📞 Getting Help

**Format Questions?**
→ Read EXTRACTION_FORMAT_GUIDE.md

**Quick Example?**
→ Check QUICK_START_EXTRACTION.md

**How to Integrate?**
→ See QUICK_START_EXTRACTION.md use cases

**See It Working?**
→ Run `python test_extraction_format.py`

**Technical Details?**
→ Review MODIFICATIONS_SUMMARY.md

---

## 🎯 Key Points

✓ **Confidence Scores** (0-100) tell you how certain each extraction is
✓ **References** (page, section, title) show exactly where the value came from
✓ **Structured Format** makes it easy to filter, sort, and process data
✓ **Backward Compatible** - old code still works, no changes needed
✓ **Production Ready** - fully tested and validated

---

## 📝 Version Info

- **Version**: 1.0
- **Date**: 2026-09-13
- **Status**: ✅ Complete and tested
- **Python**: 3.7+
- **FastAPI**: 0.68.0+

---

**Print this page for quick reference!**

Last updated: 2026-09-13

# Quick Start: Extraction with Confidence Scores and References

## 🚀 Getting Started

The ContractIQ API now returns extracted contract parameters with confidence scores and document references. Here's how to use it:

---

## Basic API Call

### Python Example

```python
import requests

# Extract contract fields
response = requests.post(
    'http://localhost:8000/extract',
    json={
        "markdown_file_path": "/path/to/contract.md"
    }
)

result = response.json()

# Access extracted parameters
for param in result['extracted_parameters']:
    print(f"{param['parameter_name']}: {param['parameter_value']}")
    print(f"  Confidence: {param['confidence_score']}%")
    print(f"  Location: {param['reference']['section_title']} (Page {param['reference']['page_num']})")
```

### cURL Example

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_file_path": "/path/to/contract.md"
  }' | jq '.extracted_parameters[]'
```

### JavaScript Example

```javascript
const response = await fetch('http://localhost:8000/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        markdown_file_path: '/path/to/contract.md'
    })
});

const result = await response.json();
result.extracted_parameters.forEach(param => {
    console.log(`${param.parameter_name}: ${param.parameter_value}`);
    console.log(`Confidence: ${param.confidence_score}%`);
});
```

---

## Response Format

```json
{
    "success": true,
    "message": "Contract fields extracted successfully",
    "extraction_id": 1,
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
    ],
    "timestamp": "2026-09-12T19:30:00"
}
```

---

## Common Use Cases

### 1. Filter by Confidence Score

```python
# Only use high-confidence extractions
high_confidence_params = [
    p for p in result['extracted_parameters']
    if p['confidence_score'] >= 90
]

for param in high_confidence_params:
    print(f"✓ {param['parameter_name']}: {param['parameter_value']}")
```

### 2. Find Parameter by Name

```python
# Get a specific parameter
params_by_name = {p['parameter_name']: p for p in result['extracted_parameters']}

if 'contract_price' in params_by_name:
    price = params_by_name['contract_price']
    print(f"Contract Price: ${price['parameter_value']}")
    print(f"Found at: {price['reference']['section_title']}")
```

### 3. Group by Confidence Level

```python
from collections import defaultdict

confidence_groups = defaultdict(list)

for param in result['extracted_parameters']:
    if param['confidence_score'] >= 90:
        level = "Very High"
    elif param['confidence_score'] >= 70:
        level = "High"
    elif param['confidence_score'] >= 50:
        level = "Medium"
    else:
        level = "Low"
    
    confidence_groups[level].append(param)

for level, params in confidence_groups.items():
    print(f"\n{level} Confidence ({len(params)} parameters):")
    for p in params:
        print(f"  • {p['parameter_name']}")
```

### 4. Export to CSV

```python
import csv

with open('extraction_results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            'parameter_name',
            'parameter_value',
            'confidence_score',
            'page_num',
            'section_number',
            'section_title'
        ]
    )
    writer.writeheader()
    
    for param in result['extracted_parameters']:
        writer.writerow({
            'parameter_name': param['parameter_name'],
            'parameter_value': param['parameter_value'],
            'confidence_score': param['confidence_score'],
            'page_num': param['reference']['page_num'],
            'section_number': param['reference']['section_number'],
            'section_title': param['reference']['section_title']
        })
```

### 5. Track Reference Information

```python
# Group parameters by page
params_by_page = defaultdict(list)

for param in result['extracted_parameters']:
    page = param['reference']['page_num']
    params_by_page[page].append(param)

for page in sorted(params_by_page.keys()):
    print(f"\nPage {page}:")
    for param in params_by_page[page]:
        print(f"  [{param['reference']['section_number']}] {param['parameter_name']}")
```

---

## Data Types

### Parameter Structure

```python
{
    "parameter_name": str,           # Field name (e.g., "contract_price")
    "parameter_value": str or null,  # Extracted value
    "confidence_score": int,         # 0-100 (higher = more confident)
    "reference": {
        "page_num": int or null,     # Page number where found
        "section_number": str or null, # Section ID (e.g., "3.2")
        "section_title": str or null   # Section title
    }
}
```

---

## Confidence Score Reference

| Score Range | Level | Use Case |
|------------|-------|----------|
| 90-100 | Very High | Use directly in automated systems |
| 70-89 | High | Use with minor manual verification |
| 50-69 | Medium | Flag for review before use |
| 0-49 | Low | Requires manual review/extraction |

---

## Error Handling

```python
try:
    response = requests.post('http://localhost:8000/extract', json=request_data)
    response.raise_for_status()
    
    result = response.json()
    
    if result['success']:
        params = result['extracted_parameters']
        # Process parameters
    else:
        print(f"Extraction failed: {result['message']}")
        
except requests.exceptions.RequestException as e:
    print(f"API error: {e}")
except KeyError as e:
    print(f"Response format error: {e}")
```

---

## Best Practices

✅ **DO:**
- Filter by confidence scores before using in critical systems
- Store reference information for audit trails
- Handle null values gracefully
- Cache results to reduce API calls

❌ **DON'T:**
- Assume all parameters are present
- Use low-confidence scores without review
- Ignore reference information
- Overwrite original document data

---

## Testing

Test the format locally:

```bash
python test_extraction_format.py
```

This will display:
- Sample extraction results
- Parameter structure
- Confidence filtering
- Summary statistics
- Export examples

---

## Next Steps

1. **Read Full Documentation**: [EXTRACTION_FORMAT_GUIDE.md](./EXTRACTION_FORMAT_GUIDE.md)
2. **Review Code Changes**: [MODIFICATIONS_SUMMARY.md](./MODIFICATIONS_SUMMARY.md)
3. **Integrate into Your App**: Update your client code
4. **Set Up Monitoring**: Track extraction quality metrics

---

## Troubleshooting

### No extracted_parameters in response?
- Ensure the contract file is valid markdown
- Check that the file path exists
- Verify the LLM API is accessible

### Low confidence scores?
- Check contract is clear and well-formatted
- Ensure all fields are explicitly stated
- Review section titles and numbers

### Missing reference information?
- Not all contracts have page numbers
- Some documents may not have section identifiers
- This is normal and doesn't affect extracted values

---

## Support Resources

- **Full Guide**: [EXTRACTION_FORMAT_GUIDE.md](./EXTRACTION_FORMAT_GUIDE.md)
- **Test Examples**: [test_extraction_format.py](./test_extraction_format.py)
- **API Docs**: Visit `http://localhost:8000/docs`
- **Source Code**: Check `models/contract_extract.py`, `prompts.py`, `services/contract_extractor.py`

---

## Code Examples Repository

Check the `test_extraction_format.py` file for more complete examples including:
- Parameter filtering
- CSV export
- JSON export
- Confidence-based processing
- Summary statistics

---

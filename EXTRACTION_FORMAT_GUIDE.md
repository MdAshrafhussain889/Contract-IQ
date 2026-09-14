# Contract Extraction Format Guide

## Overview

The ContractIQ API now returns extracted parameters in a structured format that includes:
- **parameter_name**: The name of the extracted field
- **parameter_value**: The extracted value from the contract
- **confidence_score**: A score (0-100) indicating the confidence level of the extraction
- **reference**: Location information including page number, section number, and section title

## Response Format

### Basic Structure

```json
{
    "parameter_name": "field_name",
    "parameter_value": "extracted_value",
    "confidence_score": 95,
    "reference": {
        "page_num": 1,
        "section_number": "2.1",
        "section_title": "Property Details"
    }
}
```

### Full API Response

```json
{
    "success": true,
    "message": "Contract fields extracted successfully",
    "extraction_id": 1,
    "extracted_fields": {
        "id": 1,
        "markdown_filename": "contract_extracted.md",
        "folder_path": "/path/to/contract",
        "extraction_timestamp": "2026-09-12T19:30:00",
        "subject_to_lease": "Yes — tenanted",
        "date_of_tenancy": "2026-11-14",
        "contract_price": 1285000,
        ...
    },
    "extracted_parameters": [
        {
            "parameter_name": "subject_to_lease",
            "parameter_value": "Yes — tenanted",
            "confidence_score": 95,
            "reference": {
                "page_num": 1,
                "section_number": "2.1",
                "section_title": "Property Details"
            }
        },
        {
            "parameter_name": "contract_price",
            "parameter_value": "1285000",
            "confidence_score": 98,
            "reference": {
                "page_num": 2,
                "section_number": "3.2",
                "section_title": "Purchase Price"
            }
        },
        ...
    ],
    "timestamp": "2026-09-12T19:30:00"
}
```

## Confidence Score Guidelines

The confidence score reflects how certain the extraction is based on the contract content:

| Score Range | Interpretation | Description |
|------------|-----------------|-------------|
| 90-100 | Very High | Information explicitly and clearly stated in the contract |
| 70-89 | High | Information reasonably clear but requires minor interpretation |
| 50-69 | Medium | Information partially clear or requires some context inference |
| 0-49 | Low | Information unclear, uncertain, or requires significant inference |

## Reference Information

The reference object contains location data for where the extracted value was found:

- **page_num** (integer or null): The page number in the document where the information was found
- **section_number** (string or null): The section/clause number (e.g., "2.1", "Article 3", "Clause 5.2")
- **section_title** (string or null): The human-readable title of the section or clause (e.g., "Property Details", "Purchase Price", "Settlement Terms")

## Extracted Fields

The API extracts the following 12 contract fields:

1. **subject_to_lease** - Whether property is subject to lease/tenancy
2. **date_of_tenancy** - Date tenancy begins
3. **contract_price** - Agreed purchase price
4. **deposit_amount** - Required deposit
5. **deposit_due_date** - Deposit payment due date
6. **subject_to_finance** - Finance approval condition
7. **settlement_date** - Settlement/completion date
8. **gst_clause** - GST clause details
9. **terms_contract** - Key contractual terms
10. **default_provisions** - Default/breach provisions
11. **due_date_extension** - Extension provisions
12. **special_conditions** - Special/unique clauses

## Database Storage

The extracted parameters are stored in the database as a JSON array in the `extracted_parameters` field:

```json
[
    {
        "parameter_name": "subject_to_lease",
        "parameter_value": "Yes — tenanted",
        "confidence_score": 95,
        "reference": {
            "page_num": 1,
            "section_number": "2.1",
            "section_title": "Property Details"
        }
    },
    ...
]
```

## Example Usage

### Python

```python
import requests
import json

# Extract contract fields
response = requests.post(
    'http://localhost:8000/extract',
    json={"markdown_file_path": "/path/to/contract.md"}
)

result = response.json()

# Access extracted parameters
if result['success']:
    for param in result['extracted_parameters']:
        print(f"Field: {param['parameter_name']}")
        print(f"Value: {param['parameter_value']}")
        print(f"Confidence: {param['confidence_score']}%")
        print(f"Location: Page {param['reference']['page_num']}, Section {param['reference']['section_number']}")
        print(f"Section Title: {param['reference']['section_title']}")
        print("---")
```

### cURL

```bash
curl -X POST "http://localhost:8000/extract" \
  -H "Content-Type: application/json" \
  -d '{"markdown_file_path": "/path/to/contract.md"}' \
  | jq '.extracted_parameters[] | {parameter_name, parameter_value, confidence_score, reference}'
```

### JavaScript

```javascript
fetch('http://localhost:8000/extract', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ markdown_file_path: '/path/to/contract.md' })
})
.then(r => r.json())
.then(data => {
    data.extracted_parameters.forEach(param => {
        console.log(`${param.parameter_name}: ${param.parameter_value}`);
        console.log(`Confidence: ${param.confidence_score}%`);
        console.log(`Location: Page ${param.reference.page_num}, Section ${param.reference.section_number}`);
    });
});
```

## Data Models

### ExtractedParameter (Pydantic Model)

```python
from pydantic import BaseModel
from typing import Optional

class Reference(BaseModel):
    page_num: Optional[int] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None

class ExtractedParameter(BaseModel):
    parameter_name: str
    parameter_value: Optional[str] = None
    confidence_score: int  # 0-100
    reference: Reference = Reference()
```

## Integration Notes

1. **Backward Compatibility**: The existing `extracted_fields` object is still returned alongside the new `extracted_parameters` array for backward compatibility.

2. **Null Values**: When a parameter cannot be extracted, `parameter_value` will be null and `confidence_score` will be 0.

3. **Reference Information**: If reference information cannot be determined from the document, the reference object fields may be null.

4. **Confidence Scoring**: Confidence scores are calculated by the LLM based on how clearly the information appears in the contract.

5. **JSON Storage**: The extracted parameters are persisted in the database as a JSON string for reliable storage and retrieval.

## API Endpoints

### Extract Contract Fields

**POST** `/extract`

**Request:**
```json
{
    "markdown_file_path": "/path/to/contract.md"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Contract fields extracted successfully",
    "extraction_id": 1,
    "extracted_fields": { ... },
    "extracted_parameters": [ ... ],
    "timestamp": "2026-09-12T19:30:00"
}
```

### List Extractions

**GET** `/extractions`

Returns all extraction records from the database.

### Get Extraction by ID

**GET** `/extractions/{extraction_id}`

Returns a specific extraction record with all extracted parameters.

## Error Handling

If extraction fails, the API will return an error response:

```json
{
    "detail": "Error extracting contract: [error message]"
}
```

Common error scenarios:
- File not found (400)
- Invalid markdown format (400)
- API rate limiting (429)
- Internal server error (500)

## Future Enhancements

- Support for multi-language document extraction
- Custom confidence thresholds for filtering
- Export extracted parameters to CSV/Excel
- Batch extraction for multiple documents
- Parameter matching and deduplication across documents

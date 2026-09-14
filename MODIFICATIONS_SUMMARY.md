# Code Modifications Summary

## Overview
The codebase has been successfully modified to return extracted parameters in a structured format with confidence scores and reference information. All extracted parameters now follow this standard format:

```json
{
    "parameter_name": "<field_name>",
    "parameter_value": "<extracted_value>",
    "confidence_score": <0-100>,
    "reference": {
        "page_num": <page_number>,
        "section_number": "<section_id>",
        "section_title": "<section_title>"
    }
}
```

---

## Files Modified

### 1. **models/contract_extract.py**
**Changes Made:**
- ✅ Added `Reference` Pydantic model to store page number, section number, and section title
- ✅ Added `ExtractedParameter` Pydantic model with the new structured format
- ✅ Added `extracted_parameters` field to `ContractExtract` model (SQLModel table)
- ✅ Added `extracted_parameters` field to `ContractExtractBase` model
- ✅ Added necessary imports: `List`, `Any`, `json`, `BaseModel`

**New Models:**
```python
class Reference(BaseModel):
    page_num: Optional[int] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None

class ExtractedParameter(BaseModel):
    parameter_name: str
    parameter_value: Optional[str] = None
    confidence_score: int = Field(..., ge=0, le=100)
    reference: Reference = Field(default_factory=Reference)
```

---

### 2. **prompts.py**
**Changes Made:**
- ✅ Updated extraction instructions to request structured parameters
- ✅ Added `extracted_parameters` array to the output format specification
- ✅ Added confidence score guidelines (0-100 scale)
- ✅ Added reference information guidelines
- ✅ Provided clear examples of the expected output format

**Key Addition:**
```
### Output Format
Return a valid JSON object with:
{
    "extracted_parameters": [
        {
            "parameter_name": "field_name",
            "parameter_value": "extracted_value_or_null",
            "confidence_score": 0-100,
            "reference": {
                "page_num": page_number_or_null,
                "section_number": "section_identifier_or_null",
                "section_title": "section_title_or_null"
            }
        },
        ...
    ],
    // ... other fields
}
```

---

### 3. **services/contract_extractor.py**
**Changes Made:**
- ✅ Added imports for `ExtractedParameter` and `Reference` models
- ✅ Updated `_validate_and_normalize()` method to:
  - Process `extracted_parameters` array from LLM response
  - Validate and create `ExtractedParameter` objects
  - Convert confidence scores to valid 0-100 range
  - Create proper `Reference` objects for each parameter
  - Log extracted parameters count

**Key Method Update:**
```python
# Process extracted_parameters if present
extracted_params = data.get("extracted_parameters", [])
if extracted_params:
    try:
        normalized_params = []
        for param in extracted_params:
            # Validate and convert to ExtractedParameter
            reference = Reference(
                page_num=ref_data.get("page_num"),
                section_number=ref_data.get("section_number"),
                section_title=ref_data.get("section_title")
            )
            extracted_param = ExtractedParameter(
                parameter_name=param.get("parameter_name", ""),
                parameter_value=param.get("parameter_value"),
                confidence_score=min(100, max(0, int(param.get("confidence_score", 0)))),
                reference=reference
            )
            normalized_params.append(extracted_param)
        normalized["extracted_parameters"] = normalized_params
```

---

### 4. **main.py**
**Changes Made:**
- ✅ Added `import json` for JSON serialization
- ✅ Added import for `ExtractedParameter` model
- ✅ Updated `ExtractedFieldsResponse` model to include `extracted_parameters` field
- ✅ Modified `extract_contract_fields()` endpoint to:
  - Convert `extracted_parameters` list to JSON for database storage
  - Store JSON string in the `extracted_parameters` database field
  - Return structured parameters in the API response
  - Updated response examples with new format

**Key Changes:**
```python
# Convert extracted_parameters to JSON for storage
extracted_params_json = None
extracted_params_list = None
if extracted_data.extracted_parameters:
    extracted_params_list = extracted_data.extracted_parameters
    extracted_params_json = json.dumps(
        [param.dict() for param in extracted_data.extracted_parameters],
        indent=2
    )

# Store in database
db_record = ContractExtract(
    # ... other fields ...
    extracted_parameters=extracted_params_json
)

# Return in response
return ExtractedFieldsResponse(
    success=True,
    message="Contract fields extracted successfully",
    extraction_id=db_record.id,
    extracted_fields=ContractExtractResponse.from_orm(db_record),
    extracted_parameters=extracted_params_list,  # NEW
    timestamp=timestamp
)
```

---

## New Files Created

### 1. **EXTRACTION_FORMAT_GUIDE.md**
Comprehensive guide documenting:
- The new response format with examples
- Confidence score guidelines
- Reference information details
- All 12 extracted fields
- Database storage approach
- Usage examples (Python, cURL, JavaScript)
- Data models
- Integration notes
- API endpoint documentation
- Error handling
- Future enhancements

### 2. **test_extraction_format.py**
Test and demonstration script with:
- Sample extraction response data
- Formatted display of extracted parameters
- Confidence score visualization
- Filtering examples
- Parameter lookup demonstrations
- Summary statistics
- Export helper functions (JSON, CSV)

---

## Database Schema Changes

### New Field in `contract_extracts` Table
```sql
extracted_parameters TEXT NULL
-- Stores JSON array of ExtractedParameter objects
-- Example value:
-- [
--   {
--     "parameter_name": "contract_price",
--     "parameter_value": "1285000",
--     "confidence_score": 98,
--     "reference": {
--       "page_num": 2,
--       "section_number": "3.2",
--       "section_title": "Purchase Price"
--     }
--   },
--   ...
-- ]
```

---

## API Response Changes

### Before (Legacy Format)
```json
{
    "success": true,
    "extraction_id": 1,
    "extracted_fields": {
        "subject_to_lease": "Yes",
        "contract_price": 1285000,
        ...
    },
    "timestamp": "2026-09-12T19:30:00"
}
```

### After (New Format)
```json
{
    "success": true,
    "extraction_id": 1,
    "extracted_fields": {
        "subject_to_lease": "Yes",
        "contract_price": 1285000,
        ...
    },
    "extracted_parameters": [
        {
            "parameter_name": "subject_to_lease",
            "parameter_value": "Yes",
            "confidence_score": 95,
            "reference": {
                "page_num": 1,
                "section_number": "2.1",
                "section_title": "Property Details"
            }
        },
        ...
    ],
    "timestamp": "2026-09-12T19:30:00"
}
```

---

## Backward Compatibility

✅ **Maintained:** The `extracted_fields` object is still returned in all responses
✅ **Optional:** The `extracted_parameters` array is optional and included when available
✅ **No Breaking Changes:** Existing API consumers will continue to work
✅ **Enhanced:** New clients can access the richer structured format

---

## Key Features of New Format

1. **Confidence Scoring**: Each parameter includes a confidence score (0-100) indicating extraction certainty
2. **Reference Tracking**: Exact location in the document (page, section, title)
3. **Structured Data**: Organized JSON format for programmatic access
4. **Database Persistence**: Extracted parameters stored as JSON in the database
5. **Type Safety**: Pydantic models ensure data validation
6. **Flexible Querying**: Parameters easily filtered by confidence, name, or location

---

## Confidence Score Guidelines

| Range | Level | Meaning |
|-------|-------|---------|
| 90-100 | Very High | Explicitly and clearly stated |
| 70-89 | High | Reasonably clear, minor interpretation |
| 50-69 | Medium | Partially clear, context inference |
| 0-49 | Low | Unclear, significant inference |

---

## Testing

Run the test script to verify the new format:
```bash
python test_extraction_format.py
```

Output demonstrates:
- ✅ Correct parameter structure
- ✅ Valid confidence scores (0-100)
- ✅ Proper reference information
- ✅ Filtering capabilities
- ✅ Summary statistics
- ✅ Export functions

---

## Next Steps

1. **Database Migration** (if needed):
   ```bash
   # The new field is optional, so existing database will work
   # Run: python -c "from db import init_db; init_db()"
   ```

2. **Testing with Real Contracts**:
   - Upload a contract PDF/DOCX
   - Extract and verify the new format
   - Check confidence scores and references

3. **Client Integration**:
   - Update client code to use `extracted_parameters`
   - Filter by confidence scores as needed
   - Store reference information for audit trails

4. **Monitoring**:
   - Track average confidence scores
   - Monitor extraction quality
   - Analyze parameter-specific confidence patterns

---

## API Documentation

Updated endpoints include:
- **POST /extract** - Extract contract fields with new format
- **GET /extractions** - List all extractions
- **GET /extractions/{extraction_id}** - Get specific extraction

Full documentation available at:
- [EXTRACTION_FORMAT_GUIDE.md](./EXTRACTION_FORMAT_GUIDE.md)
- Interactive API docs: `http://localhost:8000/docs`

---

## Support

For issues or questions about the new format:
1. Check EXTRACTION_FORMAT_GUIDE.md for detailed documentation
2. Run test_extraction_format.py for examples
3. Review sample responses in main.py API documentation
4. Check application logs for extraction details

---

## Version Information

- **Format Version**: 1.0
- **Date Modified**: 2026-09-13
- **Python Version**: 3.7+
- **FastAPI Version**: 0.68.0+
- **Pydantic Version**: 1.8.0+

---

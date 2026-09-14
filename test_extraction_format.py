"""
Test script demonstrating the new structured extraction format.
Shows how to work with extracted parameters that include confidence scores and references.
"""

import requests
import json
from typing import Optional, List
from pydantic import BaseModel, Field


class Reference(BaseModel):
    """Reference information for extracted parameter."""
    page_num: Optional[int] = None
    section_number: Optional[str] = None
    section_title: Optional[str] = None


class ExtractedParameter(BaseModel):
    """Structured format for extracted parameters."""
    parameter_name: str
    parameter_value: Optional[str] = None
    confidence_score: int = Field(..., ge=0, le=100)
    reference: Reference = Field(default_factory=Reference)


class ExtractionResponse(BaseModel):
    """Response model for extraction with parameters."""
    success: bool
    message: str
    extraction_id: int
    extracted_parameters: Optional[List[ExtractedParameter]]
    timestamp: str


def test_extraction_format():
    """
    Test the extraction format with sample data.
    Demonstrates working with structured parameters.
    """

    # Sample response data (as would be returned from the API)
    sample_response = {
        "success": True,
        "message": "Contract fields extracted successfully",
        "extraction_id": 1,
        "extracted_fields": {
            "id": 1,
            "markdown_filename": "contract_extracted.md",
            "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/contract",
            "extraction_timestamp": "2026-09-12T19:30:00",
            "subject_to_lease": "Yes — tenanted",
            "date_of_tenancy": "2026-11-14",
            "contract_price": 1285000,
            "deposit_amount": 128500,
            "deposit_due_date": "2026-09-13",
            "subject_to_finance": True,
            "settlement_date": "30 days from signing",
            "gst_clause": "Price is GST inclusive",
            "terms_contract": "Standard terms apply",
            "default_provisions": "Interest 12% p.a. on default",
            "due_date_extension": None,
            "special_conditions": "14 identified — 3 affect purchaser"
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
            {
                "parameter_name": "deposit_amount",
                "parameter_value": "128500",
                "confidence_score": 97,
                "reference": {
                    "page_num": 2,
                    "section_number": "3.3",
                    "section_title": "Deposit Requirements"
                }
            },
            {
                "parameter_name": "deposit_due_date",
                "parameter_value": "2026-09-13",
                "confidence_score": 92,
                "reference": {
                    "page_num": 2,
                    "section_number": "3.4",
                    "section_title": "Payment Terms"
                }
            },
            {
                "parameter_name": "subject_to_finance",
                "parameter_value": "true",
                "confidence_score": 88,
                "reference": {
                    "page_num": 3,
                    "section_number": "4.1",
                    "section_title": "Conditions Precedent"
                }
            },
            {
                "parameter_name": "settlement_date",
                "parameter_value": "30 days from signing",
                "confidence_score": 85,
                "reference": {
                    "page_num": 3,
                    "section_number": "4.2",
                    "section_title": "Completion Date"
                }
            }
        ],
        "timestamp": "2026-09-12T19:30:00"
    }

    print("=" * 80)
    print("CONTRACT EXTRACTION FORMAT TEST")
    print("=" * 80)
    print()

    # Display overall extraction info
    print(f"✓ Extraction successful: {sample_response['success']}")
    print(f"  Message: {sample_response['message']}")
    print(f"  Extraction ID: {sample_response['extraction_id']}")
    print(f"  Timestamp: {sample_response['timestamp']}")
    print()

    # Display extracted parameters in structured format
    print("=" * 80)
    print("EXTRACTED PARAMETERS (Structured Format)")
    print("=" * 80)
    print()

    if sample_response['extracted_parameters']:
        # Create response object for validation
        response = ExtractionResponse(**sample_response)

        # Display each parameter
        for i, param in enumerate(response.extracted_parameters, 1):
            print(f"[{i}] {param.parameter_name.upper()}")
            print(f"    Value: {param.parameter_value}")
            print(f"    Confidence: {param.confidence_score}%", end="")

            # Add confidence level indicator
            if param.confidence_score >= 90:
                print(" ✓ Very High")
            elif param.confidence_score >= 70:
                print(" ✓ High")
            elif param.confidence_score >= 50:
                print(" ⚠ Medium")
            else:
                print(" ✗ Low")

            # Display reference information
            if param.reference:
                print(f"    Reference:")
                if param.reference.page_num:
                    print(f"      • Page: {param.reference.page_num}")
                if param.reference.section_number:
                    print(f"      • Section: {param.reference.section_number}")
                if param.reference.section_title:
                    print(f"      • Title: {param.reference.section_title}")

            print()

    # Demonstrate filtering by confidence score
    print("=" * 80)
    print("FILTERED RESULTS (Confidence >= 90%)")
    print("=" * 80)
    print()

    high_confidence = [
        p for p in response.extracted_parameters
        if p.confidence_score >= 90
    ]

    for param in high_confidence:
        print(f"• {param.parameter_name}: {param.parameter_value}")

    print()
    print(f"Found {len(high_confidence)} parameters with high confidence")
    print()

    # Demonstrate accessing by parameter name
    print("=" * 80)
    print("PARAMETER LOOKUP EXAMPLE")
    print("=" * 80)
    print()

    params_by_name = {p.parameter_name: p for p in response.extracted_parameters}

    if 'contract_price' in params_by_name:
        price_param = params_by_name['contract_price']
        print(f"Contract Price: ${price_param.parameter_value}")
        print(f"  • Confidence: {price_param.confidence_score}%")
        print(f"  • Location: {price_param.reference.section_title} (Page {price_param.reference.page_num})")
        print()

    # Summary statistics
    print("=" * 80)
    print("EXTRACTION SUMMARY")
    print("=" * 80)
    print()

    total_params = len(response.extracted_parameters)
    avg_confidence = sum(
        p.confidence_score for p in response.extracted_parameters
    ) / total_params if total_params > 0 else 0

    params_by_confidence = {
        "Very High (90-100)": len([p for p in response.extracted_parameters if 90 <= p.confidence_score <= 100]),
        "High (70-89)": len([p for p in response.extracted_parameters if 70 <= p.confidence_score < 90]),
        "Medium (50-69)": len([p for p in response.extracted_parameters if 50 <= p.confidence_score < 70]),
        "Low (0-49)": len([p for p in response.extracted_parameters if p.confidence_score < 50])
    }

    print(f"Total Parameters Extracted: {total_params}")
    print(f"Average Confidence Score: {avg_confidence:.1f}%")
    print()
    print("Distribution by Confidence Level:")
    for level, count in params_by_confidence.items():
        print(f"  • {level}: {count} parameters")

    print()
    print("=" * 80)


def format_parameter_for_display(param: ExtractedParameter) -> dict:
    """
    Helper function to format a parameter for display in different contexts.
    """
    return {
        "parameter_name": param.parameter_name,
        "parameter_value": param.parameter_value,
        "confidence_score": param.confidence_score,
        "confidence_level": (
            "Very High" if param.confidence_score >= 90
            else "High" if param.confidence_score >= 70
            else "Medium" if param.confidence_score >= 50
            else "Low"
        ),
        "reference": {
            "page_num": param.reference.page_num,
            "section_number": param.reference.section_number,
            "section_title": param.reference.section_title
        }
    }


def export_parameters_to_json(params: List[ExtractedParameter], filename: str = "extracted_params.json"):
    """
    Export extracted parameters to JSON file.
    """
    formatted_params = [format_parameter_for_display(p) for p in params]
    with open(filename, 'w') as f:
        json.dump(formatted_params, f, indent=2)
    print(f"✓ Exported {len(params)} parameters to {filename}")


def export_parameters_to_csv(params: List[ExtractedParameter], filename: str = "extracted_params.csv"):
    """
    Export extracted parameters to CSV file.
    """
    import csv

    with open(filename, 'w', newline='') as f:
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

        for param in params:
            writer.writerow({
                'parameter_name': param.parameter_name,
                'parameter_value': param.parameter_value,
                'confidence_score': param.confidence_score,
                'page_num': param.reference.page_num,
                'section_number': param.reference.section_number,
                'section_title': param.reference.section_title
            })

    print(f"✓ Exported {len(params)} parameters to {filename}")


if __name__ == "__main__":
    test_extraction_format()

    # Uncomment to test export functions
    # sample_params = [...]  # List of ExtractedParameter objects
    # export_parameters_to_json(sample_params)
    # export_parameters_to_csv(sample_params)

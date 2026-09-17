"""
SQLModel schema for contract data extraction.
Stores extracted contract fields in SQLite database.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlmodel import SQLModel, Field

from models.schemas import ExtractedParameter


class ContractExtract(SQLModel, table=True):
    """
    SQLModel for contract extraction persistence.
    Stores extracted contract fields in SQLite database.
    """
    __tablename__ = "contract_extracts"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)

    # Extracted fields
    subject_to_lease: Optional[str] = Field(
        None,
        description="Whether property is subject to lease/tenancy"
    )
    date_of_tenancy: Optional[str] = Field(
        None,
        description="Date tenancy begins or relevant tenancy date (YYYY-MM-DD)"
    )
    contract_price: Optional[float] = Field(
        None,
        description="Agreed contract/purchase price"
    )
    deposit_amount: Optional[float] = Field(
        None,
        description="Required deposit amount"
    )
    deposit_due_date: Optional[str] = Field(
        None,
        description="Date by which deposit must be paid (YYYY-MM-DD)"
    )
    subject_to_finance: Optional[bool] = Field(
        None,
        description="Whether contract is subject to finance approval"
    )
    settlement_date: Optional[str] = Field(
        None,
        description="Agreed settlement/completion date"
    )
    gst_clause: Optional[str] = Field(
        None,
        description="GST clause or provision details"
    )
    terms_contract: Optional[str] = Field(
        None,
        description="Key contractual terms and conditions"
    )
    default_provisions: Optional[str] = Field(
        None,
        description="Provisions for default/breach scenarios"
    )
    due_date_extension: Optional[str] = Field(
        None,
        description="Provisions for extension of payment/settlement dates"
    )
    special_conditions: Optional[str] = Field(
        None,
        description="Special conditions or clauses in the contract"
    )

    # Metadata
    markdown_filename: str = Field(..., description="Filename of markdown file extracted from")
    folder_path: str = Field(..., description="Path to the document folder")
    extraction_timestamp: str = Field(..., description="When extraction was performed")

    # New structured format for extracted parameters
    extracted_parameters: Optional[str] = Field(
        None,
        description="JSON array of extracted parameters with confidence scores and references"
    )


class ContractExtractBase(SQLModel):
    """Base schema for contract extraction (without id and metadata)."""
    subject_to_lease: Optional[str] = None
    date_of_tenancy: Optional[str] = None
    contract_price: Optional[float] = None
    deposit_amount: Optional[float] = None
    deposit_due_date: Optional[str] = None
    subject_to_finance: Optional[bool] = None
    settlement_date: Optional[str] = None
    gst_clause: Optional[str] = None
    terms_contract: Optional[str] = None
    default_provisions: Optional[str] = None
    due_date_extension: Optional[str] = None
    special_conditions: Optional[str] = None
    extracted_parameters: Optional[List[ExtractedParameter]] = None


class ContractExtractResponse(ContractExtract):
    """Response model for API responses."""
    pass

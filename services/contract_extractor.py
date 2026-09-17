"""
Contract extraction service using OpenAI GPT API with structured output.
Extracts contract fields and validates against Pydantic schema.
"""

import os
import json
import logging
import requests
from pathlib import Path
from typing import Optional
from datetime import datetime

from pydantic import ValidationError

from models.contract_extract import ContractExtractBase
from models.schemas import ExtractedParameter, Reference
from prompts import build_extraction_prompt

# Setup logging
logger = logging.getLogger(__name__)


class ContractExtractionError(Exception):
    """Custom exception for extraction errors."""
    pass


class InvalidMarkdownFileError(ValueError):
    """Raised when the supplied path is not a valid markdown file."""
    pass


class MissingApiKeyError(ValueError):
    """Raised when the OpenAI API key is not configured."""
    pass


class ContractExtractor:
    """Service for extracting contract data using OpenAI GPT."""

    def __init__(self):
        """Initialize the extractor with API key."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            raise MissingApiKeyError("OPENAI_API_KEY environment variable not set")

        self.base_url = "https://api.openai.com/v1"
        self.model = "gpt-4o-mini"  # Using GPT-4o mini for best performance and cost

    def read_markdown_file(self, file_path: str, base_dir: Optional[str] = None) -> str:
        """
        Read markdown file from the tempfolder structure.

        Args:
            file_path: Path to the markdown file
            base_dir: If provided, the file must live inside this directory

        Returns:
            File content as string

        Raises:
            FileNotFoundError: If file doesn't exist
            InvalidMarkdownFileError: If the file is not markdown or escapes base_dir
            IOError: If file cannot be read
        """
        path = Path(file_path).resolve()

        if base_dir is not None:
            base = Path(base_dir).resolve()
            if not path.is_relative_to(base):
                raise InvalidMarkdownFileError(
                    f"File must be inside the temporary directory: {file_path}"
                )

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() != ".md":
            raise InvalidMarkdownFileError(f"File must be markdown (.md): {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info(f"Read markdown file: {file_path} ({len(content)} bytes)")
            return content
        except IOError as e:
            raise IOError(f"Cannot read file {file_path}: {str(e)}")

    def extract_fields(self, markdown_content: str) -> ContractExtractBase:
        """
        Extract contract fields using OpenAI GPT API with structured output.

        Args:
            markdown_content: The contract content in markdown format

        Returns:
            ContractExtractBase with validated extracted fields

        Raises:
            ContractExtractionError: If extraction or validation fails
        """
        try:
            # Build the extraction prompt
            prompt = build_extraction_prompt(markdown_content)

            logger.info("Sending extraction request to OpenAI API...")

            # Call OpenAI API with structured output using requests
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "max_tokens": 2000,
                "temperature": 0,  # Deterministic output for extraction
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a contract data extraction expert. Extract the specified fields from contracts and return valid JSON only."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )

            response.raise_for_status()
            response_data = response.json()

            # Extract the response text
            response_text = response_data["choices"][0]["message"]["content"]

            logger.info(f"Received response from OpenAI: {len(response_text)} characters")

            # Parse JSON response
            extracted_data = self._parse_json_response(response_text)

            # Validate and convert to ContractExtractBase
            validated_data = self._validate_and_normalize(extracted_data)

            logger.info("Successfully extracted and validated contract fields")
            return validated_data

        except json.JSONDecodeError as e:
            raise ContractExtractionError(f"Failed to parse LLM response as JSON: {str(e)}")
        except ValidationError as e:
            raise ContractExtractionError(f"Validation error: {str(e)}")
        except Exception as e:
            raise ContractExtractionError(f"Unexpected error during extraction: {str(e)}")

    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse JSON from LLM response, handling markdown code blocks.

        Args:
            response_text: Raw response from LLM

        Returns:
            Parsed dictionary
        """
        # Remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
        if response_text.startswith("```"):
            response_text = response_text[3:]  # Remove ```
        if response_text.endswith("```"):
            response_text = response_text[:-3]  # Remove trailing ```

        response_text = response_text.strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse: {response_text[:200]}")
            raise

    def _validate_and_normalize(self, data: dict) -> ContractExtractBase:
        """
        Validate extracted data and normalize types.

        Args:
            data: Raw extracted data

        Returns:
            Validated ContractExtractBase object
        """
        # Normalize the data
        normalized = {}

        # Process extracted_parameters if present
        extracted_params = data.get("extracted_parameters", [])
        if extracted_params:
            try:
                normalized_params = []
                for param in extracted_params:
                    if isinstance(param, dict):
                        # Validate and create ExtractedParameter object
                        ref_data = param.get("reference", {})
                        reference = Reference(
                            page_num=ref_data.get("page_num"),
                            section_number=ref_data.get("section_number"),
                            section_title=ref_data.get("section_title")
                        )

                        raw_value = param.get("parameter_value")
                        extracted_param = ExtractedParameter(
                            parameter_name=str(param.get("parameter_name", "")),
                            parameter_value=None if raw_value is None else str(raw_value),
                            confidence_score=min(100, max(0, int(param.get("confidence_score", 0)))),
                            reference=reference
                        )
                        normalized_params.append(extracted_param)

                normalized["extracted_parameters"] = normalized_params
                logger.info(f"Extracted {len(normalized_params)} structured parameters with confidence scores")
            except Exception as e:
                logger.warning(f"Failed to process extracted_parameters: {str(e)}")
                normalized["extracted_parameters"] = None

        # String fields (return as-is)
        string_fields = [
            "subject_to_lease",
            "gst_clause",
            "terms_contract",
            "default_provisions",
            "due_date_extension",
            "special_conditions"
        ]

        for field in string_fields:
            value = data.get(field)
            if value and value != "null" and value != "None":
                normalized[field] = str(value).strip() if value else None
            else:
                normalized[field] = None

        # Date fields (YYYY-MM-DD format)
        date_fields = ["date_of_tenancy", "deposit_due_date", "settlement_date"]
        for field in date_fields:
            value = data.get(field)
            if value and value != "null" and value != "None":
                # If it's already a date string in YYYY-MM-DD format, keep it
                if isinstance(value, str) and len(value) == 10 and value.count("-") == 2:
                    normalized[field] = value
                else:
                    normalized[field] = None
            else:
                normalized[field] = None

        # Numeric fields
        numeric_fields = ["contract_price", "deposit_amount"]
        for field in numeric_fields:
            value = data.get(field)
            if value and value != "null" and value != "None":
                try:
                    # Convert to float
                    if isinstance(value, (int, float)):
                        normalized[field] = float(value)
                    elif isinstance(value, str):
                        # Remove currency symbols and commas
                        clean_value = value.replace("$", "").replace(",", "").strip()
                        if clean_value:
                            normalized[field] = float(clean_value)
                        else:
                            normalized[field] = None
                    else:
                        normalized[field] = None
                except (ValueError, TypeError):
                    normalized[field] = None
            else:
                normalized[field] = None

        # Boolean fields
        boolean_fields = ["subject_to_finance"]
        for field in boolean_fields:
            value = data.get(field)
            if value is None or value == "null" or value == "None":
                normalized[field] = None
            elif isinstance(value, bool):
                normalized[field] = value
            elif isinstance(value, str):
                if value.lower() in ["true", "yes", "1"]:
                    normalized[field] = True
                elif value.lower() in ["false", "no", "0"]:
                    normalized[field] = False
                else:
                    normalized[field] = None
            else:
                normalized[field] = None

        # Validate using Pydantic
        return ContractExtractBase(**normalized)

    def extract_from_file(
        self,
        markdown_file_path: str,
        base_dir: Optional[str] = None
    ) -> ContractExtractBase:
        """
        Extract contract fields from a markdown file.

        Args:
            markdown_file_path: Path to the markdown file
            base_dir: If provided, the file must live inside this directory

        Returns:
            ContractExtractBase with validated extracted fields
        """
        # Read the file
        content = self.read_markdown_file(markdown_file_path, base_dir=base_dir)

        # Extract fields
        return self.extract_fields(content)


# Global extractor instance
_extractor = None


def get_extractor() -> ContractExtractor:
    """Get or create the global extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = ContractExtractor()
    return _extractor

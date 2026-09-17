"""
FastAPI endpoint for document to Markdown conversion.
Accepts PDF, DOCX, and DOC files and converts them to Markdown format.
"""

import os
import shutil
import json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from dotenv import load_dotenv

# Load environment variables from .env file
# Use absolute path to ensure .env is loaded regardless of working directory
_env_file = Path(__file__).parent / ".env"
load_dotenv(_env_file, override=True)

# Verify API key is loaded
_api_key_check = os.getenv("OPENAI_API_KEY")
if _api_key_check and _api_key_check != "your_openai_api_key_here":
    print("OPENAI_API_KEY loaded successfully", flush=True)
else:
    print("WARNING: OPENAI_API_KEY not found in environment", flush=True)

from document_converter import (
    DocumentConverter,
    DocumentConversionError,
    ConversionServiceError,
)
from models.contract_extract import ContractExtract, ContractExtractResponse, ContractExtractBase
from models.schemas import ExtractedParameter
from services.contract_extractor import (
    get_extractor,
    ContractExtractionError,
    InvalidMarkdownFileError,
    MissingApiKeyError,
)
from db import init_db, get_session, engine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the database (creates tables and applies lightweight migrations)
# Module-level so it runs whether launched via `python main.py` or `uvicorn main:app`.
init_db()

# ==================== Pydantic Models ====================

def _example(value):
    """Build a Pydantic v2 json_schema_extra dict carrying a Swagger example."""
    return {"example": value}


class RootResponse(BaseModel):
    """Root endpoint response model."""
    message: str = Field(..., json_schema_extra=_example("Document to Markdown Converter API"))
    status: str = Field(..., json_schema_extra=_example("running"))
    endpoints: dict = Field(
        ...,
        json_schema_extra=_example({
            "POST /convert": "Upload document and convert to markdown",
            "GET /health": "Health check",
            "GET /files": "List all converted files",
            "DELETE /cleanup": "Delete all temporary files",
            "POST /extract": "Extract contract fields from a markdown file",
            "GET /extractions": "List all stored extractions",
            "GET /extractions/{id}": "Get a stored extraction by ID"
        })
    )


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., json_schema_extra=_example("healthy"))
    temp_dir: str = Field(..., json_schema_extra=_example("tempfolder"))


class ConvertSuccessResponse(BaseModel):
    """Successful document conversion response model."""
    success: bool = Field(..., json_schema_extra=_example(True))
    message: str = Field(..., json_schema_extra=_example("Document converted successfully"))
    original_file: str = Field(..., json_schema_extra=_example("contract.pdf"))
    original_file_path: str = Field(
        ...,
        json_schema_extra=_example("tempfolder/contract/contract.pdf")
    )
    original_file_size_bytes: int = Field(..., json_schema_extra=_example(154230))
    markdown_filename: str = Field(..., json_schema_extra=_example("contract_extracted.md"))
    markdown_file_path: str = Field(
        ...,
        json_schema_extra=_example("tempfolder/contract/contract_extracted.md")
    )
    markdown_file_size_bytes: int = Field(..., json_schema_extra=_example(6919))
    file_folder: str = Field(
        ...,
        json_schema_extra=_example("tempfolder/contract")
    )
    folder_name: str = Field(..., json_schema_extra=_example("contract"))
    temp_directory: str = Field(
        ...,
        json_schema_extra=_example("tempfolder")
    )
    conversion_status: str = Field(..., json_schema_extra=_example("completed"))


class FileInfo(BaseModel):
    """Information about a converted file."""
    folder_name: str = Field(..., json_schema_extra=_example("Mujeeb_CV_6"))
    folder_path: str = Field(
        ...,
        json_schema_extra=_example("tempfolder/Mujeeb_CV_6")
    )
    original_file: Optional[str] = Field(None, json_schema_extra=_example("Mujeeb_CV_6.pdf"))
    original_file_size_bytes: int = Field(..., json_schema_extra=_example(154230))
    markdown_file: Optional[str] = Field(None, json_schema_extra=_example("Mujeeb_CV_6_extracted.md"))
    markdown_file_size_bytes: int = Field(..., json_schema_extra=_example(6919))
    total_files: int = Field(..., json_schema_extra=_example(2))
    created: float = Field(..., json_schema_extra=_example(1694529201.0))


class ListFilesResponse(BaseModel):
    """List all converted files response model."""
    success: bool = Field(..., json_schema_extra=_example(True))
    total_folders: int = Field(..., json_schema_extra=_example(3))
    temp_directory: str = Field(
        ...,
        json_schema_extra=_example("tempfolder")
    )
    folders: List[FileInfo] = Field(
        ...,
        json_schema_extra=_example([
            {
                "folder_name": "contract",
                "folder_path": "tempfolder/contract",
                "original_file": "contract.pdf",
                "original_file_size_bytes": 154230,
                "markdown_file": "contract_extracted.md",
                "markdown_file_size_bytes": 6919,
                "total_files": 2,
                "created": 1694529201.0
            }
        ])
    )


class CleanupResponse(BaseModel):
    """Cleanup response model."""
    success: bool = Field(..., json_schema_extra=_example(True))
    message: str = Field(..., json_schema_extra=_example("Cleaned up 5 items"))
    temp_directory: str = Field(
        ...,
        json_schema_extra=_example("tempfolder")
    )


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(
        ...,
        json_schema_extra=_example("Unsupported file format: .txt. Supported formats: .doc, .docx, .pdf")
    )


# ==================== Extraction Response Models ====================

class ExtractRequest(BaseModel):
    """Request model for contract field extraction."""
    markdown_file_path: str = Field(
        ...,
        json_schema_extra=_example("tempfolder/contract/contract_extracted.md"),
        description="Full path to the markdown file to extract from (must be inside the temp directory)"
    )


class ExtractedFieldsResponse(BaseModel):
    """Response model for extracted contract fields."""
    success: bool = Field(..., json_schema_extra=_example(True))
    message: str = Field(..., json_schema_extra=_example("Contract fields extracted successfully"))
    extraction_id: int = Field(..., json_schema_extra=_example(1))
    extracted_fields: ContractExtractResponse = Field(
        ...,
        description="Extracted contract fields with database record ID"
    )
    extracted_parameters: Optional[List[ExtractedParameter]] = Field(
        None,
        description="Structured extracted parameters with confidence scores and references"
    )
    timestamp: str = Field(..., json_schema_extra=_example("2026-09-12T19:30:00"))


class ExtractionListResponse(BaseModel):
    """Response model for listing extractions."""
    success: bool = Field(..., json_schema_extra=_example(True))
    total_extractions: int = Field(..., json_schema_extra=_example(5))
    extractions: List[ContractExtractResponse] = Field(
        ...,
        description="List of all extracted contracts"
    )


# Initialize FastAPI app
app = FastAPI(
    title="Document to Markdown Converter API",
    description="Convert PDF, DOCX, and DOC files to Markdown format with sample payloads for developer reference",
    version="1.0.0",
    contact={
        "name": "API Support",
        "url": "http://localhost:8000/docs"
    }
)

# CORS: allow-list configurable via the CORS_ORIGINS env var (comma-separated).
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a persistent temp directory for uploads within the project
TEMP_UPLOAD_DIR = Path(__file__).parent / "tempfolder"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_UPLOAD_DIR_RESOLVED = TEMP_UPLOAD_DIR.resolve()

# Supported file extensions (ordered tuple for stable messages)
SUPPORTED_EXTENSIONS = ('.pdf', '.docx', '.doc')
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB


@app.get(
    "/",
    response_model=RootResponse,
    tags=["Info"],
    summary="API Root Information",
    responses={
        200: {
            "description": "API information and available endpoints",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Document to Markdown Converter API",
                        "status": "running",
                        "endpoints": {
                            "POST /convert": "Upload document and convert to markdown",
                            "GET /health": "Health check",
                            "GET /files": "List all converted files",
                            "DELETE /cleanup": "Delete all temporary files",
                            "POST /extract": "Extract contract fields from a markdown file",
                            "GET /extractions": "List all stored extractions",
                            "GET /extractions/{id}": "Get a stored extraction by ID"
                        }
                    }
                }
            }
        }
    }
)
async def root():
    """
    Get API information and available endpoints.

    **Sample Response:**
    ```json
    {
      "message": "Document to Markdown Converter API",
      "status": "running",
      "endpoints": {
        "POST /convert": "Upload document and convert to markdown",
        "GET /health": "Health check",
        "GET /files": "List all converted files",
        "DELETE /cleanup": "Delete all temporary files",
        "POST /extract": "Extract contract fields from a markdown file",
        "GET /extractions": "List all stored extractions",
        "GET /extractions/{id}": "Get a stored extraction by ID"
      }
    }
    ```
    """
    return RootResponse(
        message="Document to Markdown Converter API",
        status="running",
        endpoints={
            "POST /convert": "Upload document and convert to markdown",
            "GET /health": "Health check",
            "GET /files": "List all converted files",
            "DELETE /cleanup": "Delete all temporary files",
            "POST /extract": "Extract contract fields from a markdown file",
            "GET /extractions": "List all stored extractions",
            "GET /extractions/{id}": "Get a stored extraction by ID"
        }
    )


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="API Health Check",
    responses={
        200: {
            "description": "API is healthy and running",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "temp_dir": "/Users/mac/Downloads/contractiq/tempfolder"
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Check if the API is healthy and running.

    **Use this endpoint to:**
    - Verify API connectivity
    - Check temporary directory location
    - Monitor API availability

    **Sample Response:**
    ```json
    {
      "status": "healthy",
      "temp_dir": "/Users/mac/Downloads/contractiq/tempfolder"
    }
    ```

    **Response Fields:**
    - `status`: Current API status (should be "healthy")
    - `temp_dir`: Path to the temporary folder where files are stored
    """
    return HealthCheckResponse(
        status="healthy",
        temp_dir=str(TEMP_UPLOAD_DIR)
    )


@app.post(
    "/convert",
    response_model=ConvertSuccessResponse,
    tags=["Conversion"],
    summary="Upload and Convert Document to Markdown",
    responses={
        200: {
            "description": "Document successfully converted to Markdown",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Document converted successfully",
                        "original_file": "contract.pdf",
                        "original_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract.pdf",
                        "original_file_size_bytes": 154230,
                        "markdown_filename": "contract_extracted.md",
                        "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md",
                        "markdown_file_size_bytes": 6919,
                        "file_folder": "/Users/mac/Downloads/contractiq/tempfolder/contract",
                        "folder_name": "contract",
                        "temp_directory": "/Users/mac/Downloads/contractiq/tempfolder",
                        "conversion_status": "completed"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - unsupported file format or empty document",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unsupported file format: .txt. Supported formats: .pdf, .docx, .doc"
                    }
                }
            }
        },
        413: {
            "description": "Payload too large",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File too large. Maximum size: 50.0MB"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during conversion",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error converting document: Tesseract is not installed"
                    }
                }
            }
        }
    }
)
async def convert_document(file: UploadFile = File(..., description="Document file to convert (PDF, DOCX, or DOC)")):
    """
    Upload a document and convert it to Markdown format.

    **Supported File Formats:**
    - `.pdf` - PDF documents (text-based and scanned)
    - `.docx` - Microsoft Word (2007+)
    - `.doc` - Microsoft Word (97-2003)

    **Features:**
    - Automatic OCR for scanned PDFs
    - Preserves document structure
    - Creates organized folder structure
    - Stores both original and converted files

    **Request:**
    - Content-Type: multipart/form-data
    - File parameter: Your document file (max 50 MB)

    **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/convert" \\
      -F "file=@contract.pdf"
    ```

    **Python Example:**
    ```python
    import requests

    files = {'file': open('contract.pdf', 'rb')}
    response = requests.post('http://localhost:8000/convert', files=files)
    result = response.json()
    print(f"Markdown: {result['markdown_file_path']}")
    ```

    **JavaScript Example:**
    ```javascript
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch('http://localhost:8000/convert', {
      method: 'POST',
      body: formData
    })
    .then(r => r.json())
    .then(data => console.log(data.markdown_file_path));
    ```

    **Response Fields:**
    - `success`: Boolean indicating successful conversion
    - `original_file`: Name of uploaded file
    - `original_file_path`: Full path to stored original file
    - `original_file_size_bytes`: Size of original file in bytes
    - `markdown_filename`: Generated markdown filename
    - `markdown_file_path`: Full path to generated markdown file
    - `markdown_file_size_bytes`: Size of markdown file in bytes
    - `file_folder`: Dedicated folder containing both files
    - `folder_name`: Name of the created folder
    - `temp_directory`: Path to temporary storage directory
    - `conversion_status`: Status of conversion (completed)

    **Sample Response:**
    ```json
    {
      "success": true,
      "message": "Document converted successfully",
      "original_file": "contract.pdf",
      "original_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract.pdf",
      "original_file_size_bytes": 154230,
      "markdown_filename": "contract_extracted.md",
      "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md",
      "markdown_file_size_bytes": 6919,
      "file_folder": "/Users/mac/Downloads/contractiq/tempfolder/contract",
      "folder_name": "contract",
      "temp_directory": "/Users/mac/Downloads/contractiq/tempfolder",
      "conversion_status": "completed"
    }
    ```
    """

    temp_input_path = None
    temp_output_path = None
    file_folder = None
    success = False

    try:
        # Sanitize the client-supplied filename: strip any directory components
        # so a value like "../../evil.pdf" cannot escape the temp directory.
        safe_filename = Path(file.filename).name if file.filename else ""
        if not safe_filename or safe_filename in {".", ".."}:
            raise HTTPException(status_code=400, detail="Invalid file name.")

        file_extension = Path(safe_filename).suffix.lower()
        if file_extension not in SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_extension}. "
                       f"Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        # Create a dedicated folder for this document (confined to temp dir)
        original_filename = Path(safe_filename).stem
        file_folder = (TEMP_UPLOAD_DIR / original_filename).resolve()
        temp_input_path = (file_folder / safe_filename).resolve()

        if not file_folder.is_relative_to(TEMP_UPLOAD_DIR_RESOLVED) or \
                not temp_input_path.is_relative_to(TEMP_UPLOAD_DIR_RESOLVED):
            raise HTTPException(status_code=400, detail="Invalid file name.")

        file_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created folder: {file_folder}")

        # Stream the upload to disk, enforcing the size limit as we go.
        total_bytes = 0
        with open(temp_input_path, 'wb') as f:
            while True:
                chunk = await file.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024)}MB"
                    )
                f.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="Document appears to be empty or could not be read."
            )

        logger.info(f"File uploaded to folder: {safe_filename} ({total_bytes} bytes)")

        # Convert document to markdown
        logger.info(f"Converting {safe_filename} to markdown...")
        markdown_content = DocumentConverter.convert_document(
            str(temp_input_path),
            file_extension
        )

        if not markdown_content.strip():
            raise HTTPException(
                status_code=400,
                detail="Document appears to be empty or could not be read."
            )

        # Save markdown file in the same folder
        markdown_filename = f"{original_filename}_extracted.md"
        temp_output_path = file_folder / markdown_filename

        with open(temp_output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        markdown_file_size = os.path.getsize(temp_output_path)
        original_file_size = os.path.getsize(temp_input_path)
        logger.info(f"Markdown file created: {markdown_filename} ({markdown_file_size} bytes)")

        success = True
        return ConvertSuccessResponse(
            success=True,
            message="Document converted successfully",
            original_file=safe_filename,
            original_file_path=str(temp_input_path),
            original_file_size_bytes=original_file_size,
            markdown_filename=markdown_filename,
            markdown_file_path=str(temp_output_path),
            markdown_file_size_bytes=markdown_file_size,
            file_folder=str(file_folder),
            folder_name=original_filename,
            temp_directory=str(TEMP_UPLOAD_DIR),
            conversion_status="completed"
        )

    except HTTPException as e:
        logger.error(f"Validation error: {e.detail}")
        raise e

    except DocumentConversionError as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Could not convert document: {str(e)}"
        )

    except ConversionServiceError as e:
        logger.error(f"Conversion service error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error converting document: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Conversion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error converting document. Please check server logs."
        )

    finally:
        # Do not leave partial/broken folders behind on failure.
        if not success and file_folder is not None and file_folder.exists():
            try:
                shutil.rmtree(file_folder)
            except OSError:
                logger.warning(f"Could not clean up failed conversion folder: {file_folder}")


@app.get(
    "/files",
    response_model=ListFilesResponse,
    tags=["Files"],
    summary="List All Converted Documents",
    responses={
        200: {
            "description": "Successfully retrieved list of all converted documents",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "total_folders": 2,
                        "temp_directory": "/Users/mac/Downloads/contractiq/tempfolder",
                        "folders": [
                            {
                                "folder_name": "contract",
                                "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/contract",
                                "original_file": "contract.pdf",
                                "original_file_size_bytes": 154230,
                                "markdown_file": "contract_extracted.md",
                                "markdown_file_size_bytes": 6919,
                                "total_files": 2,
                                "created": 1694529201.0
                            },
                            {
                                "folder_name": "invoice",
                                "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/invoice",
                                "original_file": "invoice.docx",
                                "original_file_size_bytes": 45600,
                                "markdown_file": "invoice_extracted.md",
                                "markdown_file_size_bytes": 3200,
                                "total_files": 2,
                                "created": 1694529250.0
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error listing files",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error listing files: Permission denied"
                    }
                }
            }
        }
    }
)
async def list_converted_files():
    """
    List all converted documents and their associated files.

    **Use this endpoint to:**
    - Browse all converted documents
    - Check file sizes and paths
    - Track conversion history
    - Verify document processing

    **cURL Example:**
    ```bash
    curl http://localhost:8000/files | jq '.'
    ```

    **Python Example:**
    ```python
    import requests

    response = requests.get('http://localhost:8000/files')
    files = response.json()

    for folder in files['folders']:
        print(f"Folder: {folder['folder_name']}")
        print(f"  Original: {folder['original_file']} ({folder['original_file_size_bytes']} bytes)")
        print(f"  Markdown: {folder['markdown_file']} ({folder['markdown_file_size_bytes']} bytes)")
    ```

    **Response Fields:**
    - `success`: Boolean indicating successful retrieval
    - `total_folders`: Number of document folders
    - `temp_directory`: Path to temporary storage directory
    - `folders`: Array of folder information objects
      - `folder_name`: Name of the document folder
      - `folder_path`: Full path to the folder
      - `original_file`: Name of original uploaded file
      - `original_file_size_bytes`: Size of original file
      - `markdown_file`: Name of converted markdown file
      - `markdown_file_size_bytes`: Size of markdown file
      - `total_files`: Number of files in folder (usually 2)
      - `created`: Timestamp when folder was created

    **Sample Response:**
    ```json
    {
      "success": true,
      "total_folders": 2,
      "temp_directory": "/Users/mac/Downloads/contractiq/tempfolder",
      "folders": [
        {
          "folder_name": "contract",
          "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/contract",
          "original_file": "contract.pdf",
          "original_file_size_bytes": 154230,
          "markdown_file": "contract_extracted.md",
          "markdown_file_size_bytes": 6919,
          "total_files": 2,
          "created": 1694529201.0
        }
      ]
    }
    ```
    """
    try:
        folders_info = []

        # Iterate through all folders in TEMP_UPLOAD_DIR
        for folder in TEMP_UPLOAD_DIR.iterdir():
            if folder.is_dir():
                original_file = None
                markdown_file = None
                original_file_size = 0
                markdown_file_size = 0

                # Find original file and markdown file in folder
                for file in folder.iterdir():
                    if file.is_file():
                        if file.name.endswith('_extracted.md'):
                            markdown_file = file.name
                            markdown_file_size = os.path.getsize(file)
                        else:
                            original_file = file.name
                            original_file_size = os.path.getsize(file)

                folders_info.append(FileInfo(
                    folder_name=folder.name,
                    folder_path=str(folder),
                    original_file=original_file,
                    original_file_size_bytes=original_file_size if original_file else 0,
                    markdown_file=markdown_file,
                    markdown_file_size_bytes=markdown_file_size if markdown_file else 0,
                    total_files=len(list(folder.iterdir())),
                    created=os.path.getctime(folder)
                ))

        return ListFilesResponse(
            success=True,
            total_folders=len(folders_info),
            temp_directory=str(TEMP_UPLOAD_DIR),
            folders=folders_info
        )

    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error listing files. Please check server logs."
        )


@app.delete(
    "/cleanup",
    response_model=CleanupResponse,
    tags=["Files"],
    summary="Delete All Converted Documents",
    responses={
        200: {
            "description": "Successfully cleaned up all temporary files",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Cleaned up 5 items",
                        "temp_directory": "/Users/mac/Downloads/contractiq/tempfolder"
                    }
                }
            }
        },
        500: {
            "description": "Error during cleanup",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error cleaning up files: Permission denied"
                    }
                }
            }
        }
    }
)
async def cleanup_temp_files():
    """
    Delete all converted documents and their folders from temporary storage.

    ⚠️ **WARNING:** This action is irreversible! All documents will be permanently deleted.

    **Use this endpoint to:**
    - Free up disk space
    - Clear old conversions
    - Reset the temporary storage

    **cURL Example:**
    ```bash
    curl -X DELETE http://localhost:8000/cleanup
    ```

    **Python Example:**
    ```python
    import requests

    response = requests.delete('http://localhost:8000/cleanup')
    result = response.json()
    print(f"Cleaned up {result['message']}")
    ```

    **Response Fields:**
    - `success`: Boolean indicating successful cleanup
    - `message`: Description of cleanup result
    - `temp_directory`: Path to temporary storage directory

    **Sample Response:**
    ```json
    {
      "success": true,
      "message": "Cleaned up 5 items",
      "temp_directory": "/Users/mac/Downloads/contractiq/tempfolder"
    }
    ```
    """
    try:
        deleted_count = 0
        for item in TEMP_UPLOAD_DIR.glob("*"):
            if item.is_file():
                os.remove(item)
                deleted_count += 1
            elif item.is_dir():
                # Remove directory and all contents
                shutil.rmtree(item)
                deleted_count += 1

        return CleanupResponse(
            success=True,
            message=f"Cleaned up {deleted_count} items",
            temp_directory=str(TEMP_UPLOAD_DIR)
        )

    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error cleaning up files. Please check server logs."
        )


# ==================== Contract Extraction Endpoints ====================

@app.post(
    "/extract",
    response_model=ExtractedFieldsResponse,
    tags=["Extraction"],
    summary="Extract Contract Fields",
    responses={
        200: {
            "description": "Contract fields extracted and stored successfully",
            "content": {
                "application/json": {
                    "example": {
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
                            }
                        ],
                        "timestamp": "2026-09-12T19:30:00"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid file path or file not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "File not found: /path/to/nonexistent/file.md"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during extraction",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error extracting contract fields: API error or validation failed"
                    }
                }
            }
        }
    }
)
async def extract_contract_fields(
    request: ExtractRequest,
    session: Session = Depends(get_session)
):
    """
    Extract 12 predefined fields from a contract Markdown file using LLM.

    **Extracted Fields:**
    1. subject_to_lease - Whether property is subject to lease/tenancy
    2. date_of_tenancy - Date tenancy begins
    3. contract_price - Agreed purchase price
    4. deposit_amount - Required deposit
    5. deposit_due_date - Deposit payment due date
    6. subject_to_finance - Finance approval condition
    7. settlement_date - Settlement/completion date
    8. gst_clause - GST clause details
    9. terms_contract - Key contractual terms
    10. default_provisions - Default/breach provisions
    11. due_date_extension - Extension provisions
    12. special_conditions - Special/unique clauses

    **Request:**
    ```json
    {
      "markdown_file_path": "/Users/mac/Downloads/contractiq/tempfolder/contract/contract_extracted.md"
    }
    ```

    **cURL Example:**
    ```bash
    curl -X POST "http://localhost:8000/extract" \\
      -H "Content-Type: application/json" \\
      -d '{"markdown_file_path": "/path/to/contract_extracted.md"}'
    ```

    **Python Example:**
    ```python
    import requests

    response = requests.post(
        'http://localhost:8000/extract',
        json={"markdown_file_path": "/path/to/contract.md"}
    )
    result = response.json()
    print(f"Extraction ID: {result['extraction_id']}")
    print(f"Fields: {result['extracted_fields']}")
    ```

    **Response Fields:**
    - `success`: Boolean indicating successful extraction
    - `message`: Status message
    - `extraction_id`: Database record ID of extraction
    - `extracted_fields`: All 12 extracted contract fields
    - `timestamp`: When extraction was performed
    """
    try:
        # Confine the requested path to the temporary directory.
        try:
            requested_path = Path(request.markdown_file_path).resolve()
        except (OSError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid markdown_file_path.")

        if not requested_path.is_relative_to(TEMP_UPLOAD_DIR_RESOLVED):
            raise HTTPException(
                status_code=400,
                detail="markdown_file_path must point to a file inside the temporary directory."
            )

        # Get the extractor
        extractor = get_extractor()

        # Extract fields from markdown file
        logger.info(f"Extracting fields from: {requested_path}")
        extracted_data = extractor.extract_from_file(
            str(requested_path), base_dir=str(TEMP_UPLOAD_DIR_RESOLVED)
        )

        # Get markdown filename from path
        markdown_filename = requested_path.name
        folder_path = str(requested_path.parent)

        # Create database record
        timestamp = datetime.now().isoformat()

        # Convert extracted_parameters to JSON for storage
        extracted_params_json = None
        extracted_params_list = None
        if extracted_data.extracted_parameters:
            extracted_params_list = extracted_data.extracted_parameters
            extracted_params_json = json.dumps(
                [param.model_dump() for param in extracted_data.extracted_parameters],
                indent=2
            )

        db_record = ContractExtract(
            subject_to_lease=extracted_data.subject_to_lease,
            date_of_tenancy=extracted_data.date_of_tenancy,
            contract_price=extracted_data.contract_price,
            deposit_amount=extracted_data.deposit_amount,
            deposit_due_date=extracted_data.deposit_due_date,
            subject_to_finance=extracted_data.subject_to_finance,
            settlement_date=extracted_data.settlement_date,
            gst_clause=extracted_data.gst_clause,
            terms_contract=extracted_data.terms_contract,
            default_provisions=extracted_data.default_provisions,
            due_date_extension=extracted_data.due_date_extension,
            special_conditions=extracted_data.special_conditions,
            markdown_filename=markdown_filename,
            folder_path=folder_path,
            extraction_timestamp=timestamp,
            extracted_parameters=extracted_params_json
        )

        # Save to database
        session.add(db_record)
        session.commit()
        session.refresh(db_record)

        logger.info(f"Extraction saved to database with ID: {db_record.id}")

        return ExtractedFieldsResponse(
            success=True,
            message="Contract fields extracted successfully",
            extraction_id=db_record.id,
            extracted_fields=ContractExtractResponse.model_validate(db_record, from_attributes=True),
            extracted_parameters=extracted_params_list,
            timestamp=timestamp
        )

    except HTTPException:
        raise

    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except InvalidMarkdownFileError as e:
        logger.error(f"Invalid markdown file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except MissingApiKeyError as e:
        logger.error(f"Missing API key: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Extraction service is not configured (missing OPENAI_API_KEY)."
        )

    except ContractExtractionError as e:
        logger.error(f"Extraction error: {str(e)}")
        raise HTTPException(status_code=500, detail="Extraction failed. Please check server logs.")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error extracting contract. Please check server logs."
        )


@app.get(
    "/extractions",
    response_model=ExtractionListResponse,
    tags=["Extraction"],
    summary="List All Extracted Contracts",
    responses={
        200: {
            "description": "Successfully retrieved list of extractions",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "total_extractions": 2,
                        "extractions": [
                            {
                                "id": 1,
                                "markdown_filename": "contract_extracted.md",
                                "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/contract",
                                "extraction_timestamp": "2026-09-12T19:30:00",
                                "subject_to_lease": "Yes — tenanted",
                                "contract_price": 1285000
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error retrieving extractions",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error retrieving extractions: Database error"
                    }
                }
            }
        }
    }
)
async def list_extractions(session: Session = Depends(get_session)):
    """
    List all extracted contracts from the database.

    **Use this endpoint to:**
    - View extraction history
    - Find previously extracted contracts
    - Verify extraction results
    - Access extracted data

    **cURL Example:**
    ```bash
    curl http://localhost:8000/extractions
    ```

    **Response includes:**
    - All 12 extracted contract fields for each extraction
    - Database record ID
    - Original markdown filename
    - Extraction timestamp

    **Sample Response:**
    ```json
    {
      "success": true,
      "total_extractions": 2,
      "extractions": [
        {
          "id": 1,
          "markdown_filename": "contract_extracted.md",
          "folder_path": "/Users/mac/Downloads/contractiq/tempfolder/contract",
          "extraction_timestamp": "2026-09-12T19:30:00",
          "subject_to_lease": "Yes — tenanted",
          "date_of_tenancy": "2026-11-14",
          "contract_price": 1285000,
          "deposit_amount": 128500,
          ...
        }
      ]
    }
    ```
    """
    try:
        # Query all extractions
        statement = select(ContractExtract).order_by(ContractExtract.id.desc())
        extractions = session.exec(statement).all()

        logger.info(f"Retrieved {len(extractions)} extractions from database")

        return ExtractionListResponse(
            success=True,
            total_extractions=len(extractions),
            extractions=[ContractExtractResponse.model_validate(e, from_attributes=True) for e in extractions]
        )

    except Exception as e:
        logger.error(f"Error retrieving extractions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving extractions. Please check server logs."
        )


@app.get(
    "/extractions/{extraction_id}",
    response_model=ContractExtractResponse,
    tags=["Extraction"],
    summary="Get Extraction by ID",
    responses={
        200: {
            "description": "Successfully retrieved extraction",
        },
        404: {
            "description": "Extraction not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Extraction not found with ID: 999"
                    }
                }
            }
        }
    }
)
async def get_extraction(extraction_id: int, session: Session = Depends(get_session)):
    """
    Get a specific extraction by ID.

    **Parameters:**
    - `extraction_id`: The database ID of the extraction

    **cURL Example:**
    ```bash
    curl http://localhost:8000/extractions/1
    ```

    **Response:**
    Returns the complete extraction record with all 12 extracted fields.
    """
    try:
        extraction = session.get(ContractExtract, extraction_id)

        if not extraction:
            raise HTTPException(
                status_code=404,
                detail=f"Extraction not found with ID: {extraction_id}"
            )

        logger.info(f"Retrieved extraction {extraction_id}")
        return ContractExtractResponse.model_validate(extraction, from_attributes=True)

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Error retrieving extraction: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving extraction. Please check server logs."
        )


if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    print("Starting Document to Markdown Converter API...")
    print(f"Temporary directory: {TEMP_UPLOAD_DIR}")

    # Database is initialized at module import (see init_db() call above).

    print("Access the API at: http://localhost:8000")
    print("API docs available at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)

"""
Document to Markdown converter module.
Supports PDF (including scanned), DOCX, and DOC formats.
"""

import os
from pathlib import Path
from typing import Optional
import pdfplumber
from PyPDF2 import PdfReader
from docx import Document
import pytesseract
from pdf2image import convert_from_path


class DocumentConverter:
    """Converts various document formats to Markdown."""

    @staticmethod
    def convert_pdf_to_markdown(pdf_path: str) -> str:
        """
        Convert PDF to Markdown.
        Handles both text-based and scanned (image-based) PDFs.
        """
        markdown_content = []

        try:
            # First try pdfplumber for text extraction
            with pdfplumber.open(pdf_path) as pdf:
                has_text = False

                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text and text.strip():
                        has_text = True
                        markdown_content.append(f"## Page {page_num}\n\n{text}\n")

                # If no text found, it's likely a scanned PDF - use OCR
                if not has_text:
                    markdown_content.append(DocumentConverter._ocr_pdf(pdf_path))

        except Exception as e:
            raise Exception(f"Error processing PDF with pdfplumber: {str(e)}")

        return "\n---\n".join(markdown_content) if markdown_content else ""

    @staticmethod
    def _ocr_pdf(pdf_path: str) -> str:
        """
        Perform OCR on PDF pages using Tesseract.
        """
        markdown_content = []

        try:
            images = convert_from_path(pdf_path, dpi=300)

            for page_num, image in enumerate(images, 1):
                text = pytesseract.image_to_string(image)
                if text.strip():
                    markdown_content.append(f"## Page {page_num}\n\n{text}\n")

        except pytesseract.TesseractNotFoundError:
            raise Exception(
                "Tesseract is not installed. For OCR support, install: "
                "brew install tesseract (macOS) or apt-get install tesseract-ocr (Linux)"
            )
        except Exception as e:
            raise Exception(f"Error during OCR: {str(e)}")

        return "\n---\n".join(markdown_content)

    @staticmethod
    def convert_docx_to_markdown(docx_path: str) -> str:
        """Convert DOCX file to Markdown."""
        markdown_content = []

        try:
            doc = Document(docx_path)

            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    # Simple markdown formatting based on style
                    if para.style.name.startswith('Heading'):
                        level = int(para.style.name[-1]) if para.style.name[-1].isdigit() else 1
                        markdown_content.append(f"{'#' * level} {text}\n")
                    else:
                        markdown_content.append(f"{text}\n")

            # Handle tables if present
            for table in doc.tables:
                markdown_content.append("\n| ")
                header_cells = [cell.text.strip() for cell in table.rows[0].cells]
                markdown_content.append(" | ".join(header_cells))
                markdown_content.append(" |\n| ")
                markdown_content.append(" | ".join(["---"] * len(header_cells)))
                markdown_content.append(" |\n")

                for row in table.rows[1:]:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    markdown_content.append("| " + " | ".join(row_cells) + " |\n")

        except Exception as e:
            raise Exception(f"Error processing DOCX: {str(e)}")

        return "".join(markdown_content)

    @staticmethod
    def convert_doc_to_markdown(doc_path: str) -> str:
        """
        Convert DOC file to Markdown.
        Note: .doc format support is limited. Converts via python-docx if possible.
        """
        try:
            # Attempt to open as docx (works for some .doc files)
            return DocumentConverter.convert_docx_to_markdown(doc_path)
        except Exception:
            raise Exception(
                "DOC format (.doc) has limited support. "
                "Please convert to DOCX (.docx) for better compatibility."
            )

    @staticmethod
    def convert_document(file_path: str, file_extension: str) -> str:
        """
        Main conversion method that routes to appropriate converter.

        Args:
            file_path: Path to the document file
            file_extension: File extension (pdf, docx, doc)

        Returns:
            Markdown content as string
        """
        file_extension = file_extension.lower().lstrip('.')

        if file_extension == 'pdf':
            return DocumentConverter.convert_pdf_to_markdown(file_path)
        elif file_extension in ['docx', 'doc']:
            return DocumentConverter.convert_docx_to_markdown(file_path)
        else:
            raise ValueError(f"Unsupported file format: .{file_extension}")

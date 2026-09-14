"""
Test script for Document to Markdown Converter API.
Tests the API endpoints with sample operations.
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

# ANSI colors for output
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'


def print_header(text):
    """Print formatted header."""
    print(f"\n{BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    """Print info message."""
    print(f"{YELLOW}ℹ {text}{RESET}")


def test_health_check():
    """Test health check endpoint."""
    print_header("Health Check")

    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print_success("Health check passed")
            print(f"Status: {data.get('status')}")
            print(f"Temp Directory: {data.get('temp_dir')}")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to API. Is the server running?")
        print(f"Make sure to start the API with: python main.py")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_root_endpoint():
    """Test root endpoint."""
    print_header("Root Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print_success("Root endpoint working")
            print(f"API Version: {data.get('version')}")
            print(f"Title: {data.get('title')}")
            print(f"Status: {data.get('status')}")
            return True
        else:
            print_error(f"Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def create_sample_pdf():
    """Create a sample PDF for testing."""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        pdf_path = "/tmp/sample_document.pdf"

        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Sample Document for Testing")
        c.drawString(100, 700, "This is a test PDF document")
        c.drawString(100, 650, "Created for API testing purposes")
        c.drawString(100, 600, "")
        c.drawString(100, 550, "Features:")
        c.drawString(120, 500, "- Multiple pages")
        c.drawString(120, 450, "- Text content")
        c.drawString(120, 400, "- Markdown conversion")
        c.save()

        print_success(f"Sample PDF created at: {pdf_path}")
        return pdf_path
    except ImportError:
        print_info("reportlab not installed. Creating text file instead.")
        # Create a text file to demonstrate (will fail but shows the process)
        return None


def test_file_conversion():
    """Test file conversion endpoint."""
    print_header("File Conversion")

    sample_file = create_sample_pdf()

    if sample_file and Path(sample_file).exists():
        try:
            with open(sample_file, 'rb') as f:
                files = {'file': f}
                print_info("Uploading file...")

                response = requests.post(
                    f"{BASE_URL}/convert",
                    files=files,
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()
                    print_success("File conversion successful")
                    print(f"Original file: {data.get('original_file')}")
                    print(f"Markdown file: {data.get('markdown_filename')}")
                    print(f"File path: {data.get('markdown_file_path')}")
                    print(f"File size: {data.get('file_size_bytes')} bytes")

                    # Try to read the generated markdown
                    markdown_path = data.get('markdown_file_path')
                    if Path(markdown_path).exists():
                        with open(markdown_path, 'r') as md:
                            content = md.read()
                            preview = content[:200] + "..." if len(content) > 200 else content
                            print(f"\nMarkdown preview:\n{preview}\n")

                    return True
                else:
                    error_data = response.json()
                    print_error(f"Conversion failed: {error_data.get('detail')}")
                    return False

        except Exception as e:
            print_error(f"Error during conversion: {str(e)}")
            return False
    else:
        print_info("Skipping file conversion test (no sample file)")
        print("Note: To test file conversion, install reportlab:")
        print("  pip install reportlab")
        return None


def test_list_files():
    """Test file listing endpoint."""
    print_header("List Files")

    try:
        response = requests.get(f"{BASE_URL}/files")
        if response.status_code == 200:
            data = response.json()
            print_success("File listing successful")
            print(f"Total files: {data.get('total_files')}")
            print(f"Temp directory: {data.get('temp_directory')}")

            if data.get('files'):
                print("\nConverted files:")
                for file_info in data.get('files', []):
                    print(f"  - {file_info.get('filename')} ({file_info.get('size_bytes')} bytes)")
            else:
                print_info("No converted files yet")

            return True
        else:
            print_error(f"File listing failed: {response.status_code}")
            return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_invalid_file():
    """Test uploading invalid file."""
    print_header("Invalid File Upload")

    try:
        # Create a temporary invalid file
        invalid_file = "/tmp/test_invalid.txt"
        with open(invalid_file, 'w') as f:
            f.write("This is not a supported format")

        with open(invalid_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{BASE_URL}/convert", files=files)

            if response.status_code == 400:
                data = response.json()
                print_success("Invalid file correctly rejected")
                print(f"Error message: {data.get('detail')}")
                return True
            else:
                print_error(f"Expected 400 error, got {response.status_code}")
                return False

    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def main():
    """Run all tests."""
    print(f"\n{BLUE}{'='*60}")
    print("  Document to Markdown Converter API - Test Suite")
    print(f"{'='*60}{RESET}\n")

    print_info(f"Testing API at: {BASE_URL}")
    print_info("Make sure the API is running with: python main.py\n")

    results = {}

    # Run tests
    results['health_check'] = test_health_check()

    if results['health_check']:  # Only continue if health check passes
        results['root_endpoint'] = test_root_endpoint()
        results['invalid_file'] = test_invalid_file()
        results['file_conversion'] = test_file_conversion()
        results['list_files'] = test_list_files()
    else:
        print_error("Cannot continue testing - API is not responding")
        return

    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    for test_name, result in results.items():
        status = "✓ PASSED" if result is True else ("✗ FAILED" if result is False else "⊘ SKIPPED")
        color = GREEN if result is True else (RED if result is False else YELLOW)
        print(f"{color}{status}{RESET} - {test_name.replace('_', ' ').title()}")

    print(f"\n{BLUE}Results: {passed} passed, {failed} failed, {skipped} skipped{RESET}\n")


if __name__ == "__main__":
    main()

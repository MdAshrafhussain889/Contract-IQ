"""Regression tests for known ContractIQ API issues (see audit report)."""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PDF = ROOT / "test_contract.pdf"


# ---------------- Issue I-06: root endpoint advertises /health ----------------

def test_root_lists_health(client):
    r = client.get("/")
    assert r.status_code == 200
    endpoints = r.json()["endpoints"]
    assert "GET /health" in endpoints
    assert "POST /convert" in endpoints


# ---------------- Health / info ----------------

def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert Path(body["temp_dir"]).exists()


# ---------------- POST /convert ----------------

def test_convert_rejects_unsupported_type(client):
    r = client.post("/convert", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_convert_rejects_empty_and_corrupt_pdf(client):
    empty = client.post("/convert", files={"file": ("empty.pdf", b"", "application/pdf")})
    assert empty.status_code == 400

    corrupt = client.post("/convert", files={"file": ("corrupt.pdf", b"not a pdf", "application/pdf")})
    assert corrupt.status_code == 400


def test_convert_valid_pdf_with_pypdf2_fallback(client):
    """The bundled test_contract.pdf has a malformed xref that breaks pdfplumber;
    the PyPDF2 fallback must make conversion succeed."""
    with open(SAMPLE_PDF, "rb") as f:
        r = client.post("/convert", files={"file": ("pytest_sample.pdf", f, "application/pdf")})
    try:
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert Path(body["markdown_file_path"]).exists()
        assert Path(body["markdown_file_path"]).stat().st_size > 0
    finally:
        shutil.rmtree(ROOT / "tempfolder" / "pytest_sample", ignore_errors=True)


def test_convert_path_traversal_blocked(client):
    """Issue I-02: a filename containing ../ must not escape tempfolder."""
    with open(SAMPLE_PDF, "rb") as f:
        r = client.post(
            "/convert",
            files={"file": ("../../pytest_evil.pdf", f, "application/pdf")},
        )
    outside = ROOT / "pytest_evil.pdf"
    try:
        assert not outside.exists(), "traversal wrote a file outside the temp directory"
        sane_path = ROOT / "tempfolder" / "pytest_evil" / "pytest_evil.pdf"
        assert sane_path.exists(), "sanitized file was not written into tempfolder"
    finally:
        if outside.exists():
            outside.unlink()
        shutil.rmtree(ROOT / "tempfolder" / "pytest_evil", ignore_errors=True)


# ---------------- POST /extract ----------------

def test_extract_rejects_path_outside_tempfolder(client):
    r = client.post("/extract", json={"markdown_file_path": str(ROOT / "README.md")})
    assert r.status_code == 400


def test_extract_rejects_non_markdown(client, temp_doc_dir, mock_openai):
    txt = temp_doc_dir / "notes.txt"
    txt.write_text("hello", encoding="utf-8")
    r = client.post("/extract", json={"markdown_file_path": str(txt)})
    assert r.status_code == 400


def test_extract_missing_api_key_is_503(client, temp_doc_dir, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import services.contract_extractor as ce
    ce._extractor = None
    md = temp_doc_dir / "contract_extracted.md"
    md.write_text("# Contract\nPrice $1,000,000.\n", encoding="utf-8")
    r = client.post("/extract", json={"markdown_file_path": str(md)})
    assert r.status_code == 503
    ce._extractor = None


def test_extract_happy_path_stores_and_reads_back(client, temp_doc_dir, mock_openai):
    md = temp_doc_dir / "contract_extracted.md"
    md.write_text(
        "# Residential Sale Contract\n\n"
        "The contract price is $1,285,000. Deposit of $128,500 due 2026-09-13.\n"
        "Subject to finance approval.\n",
        encoding="utf-8",
    )

    r = client.post("/extract", json={"markdown_file_path": str(md)})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    assert body["extracted_fields"]["contract_price"] == 1285000
    assert body["extracted_parameters"][0]["parameter_name"] == "contract_price"
    assert body["extracted_parameters"][0]["confidence_score"] == 98
    extraction_id = body["extraction_id"]
    assert isinstance(extraction_id, int) and extraction_id > 0

    listed = client.get("/extractions")
    assert listed.status_code == 200
    ids = [e["id"] for e in listed.json()["extractions"]]
    assert extraction_id in ids

    detail = client.get(f"/extractions/{extraction_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == extraction_id

    missing = client.get("/extractions/999999")
    assert missing.status_code == 404

    bad_id = client.get("/extractions/notanint")
    assert bad_id.status_code == 422


# ---------------- Migration: stale DBs gain the new column ----------------

def test_extractions_endpoint_works_after_migration(client):
    r = client.get("/extractions")
    assert r.status_code == 200
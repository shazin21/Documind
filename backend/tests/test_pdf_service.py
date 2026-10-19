import uuid
from pathlib import Path
import pymupdf as fitz
import pytest
from app.services.pdf_service import PDFService


@pytest.fixture
def sample_pdf_bytes():
    """Generates valid PDF bytes with known text content using PyMuPDF."""
    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Annual leave requests must be submitted at least two weeks in advance. "
        "Department managers are responsible for approving leave.",
    )

    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "Company vehicles require scheduled maintenance every 10,000 miles. "
        "The fleet operations manager oversees all vehicle inspections.",
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_validation_and_saving(tmp_path: Path, sample_pdf_bytes: bytes):
    service = PDFService(upload_dir=tmp_path)
    doc_id = uuid.uuid4()

    file_path, safe_name, size, content_hash = service.validate_and_save(
        document_id=doc_id,
        raw_filename="../malicious/path/Employee_Handbook.pdf",
        content=sample_pdf_bytes,
    )

    assert file_path.exists()
    assert safe_name == "Employee_Handbook.pdf"
    assert size == len(sample_pdf_bytes)
    assert len(content_hash) == 64


def test_text_and_metadata_extraction(tmp_path: Path, sample_pdf_bytes: bytes):
    service = PDFService(upload_dir=tmp_path)
    doc_id = uuid.uuid4()

    file_path, _, _, _ = service.validate_and_save(
        document_id=doc_id,
        raw_filename="sample.pdf",
        content=sample_pdf_bytes,
    )

    pages, meta = service.extract_text_and_metadata(file_path)

    assert meta["total_pages"] == 2
    assert meta["pages_with_text"] == 2
    assert meta["needs_ocr"] is False
    assert len(pages) == 2
    assert pages[0]["page"] == 1
    assert "Annual leave requests" in pages[0]["text"]
    assert pages[1]["page"] == 2
    assert "Company vehicles" in pages[1]["text"]

    service.cleanup_file(file_path)
    assert not file_path.exists()


def test_invalid_pdf_rejection(tmp_path: Path):
    service = PDFService(upload_dir=tmp_path)
    fake_content = b"This is not a real PDF file."

    with pytest.raises(ValueError, match="Invalid PDF file"):
        service.validate_and_save(
            document_id=uuid.uuid4(),
            raw_filename="fake.pdf",
            content=fake_content,
        )

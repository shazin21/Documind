import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import UUID
import pymupdf as fitz
from app.core.config import settings
from app.core.logging import logger
from app.core.security import validate_pdf_bytes, sanitize_filename


class PDFService:
    """Handles PDF validation, safe disk storage, metadata extraction, and text extraction."""

    def __init__(self, upload_dir: Optional[Path] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_and_save(
        self,
        document_id: UUID,
        raw_filename: str,
        content: bytes,
    ) -> Tuple[Path, str, int, str]:
        """
        Validates content size and format, computes SHA-256 hash, and saves to an opaque path.
        Returns: (saved_path, safe_filename, file_size, content_hash)
        """
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise ValueError(
                f"File size ({len(content) / (1024*1024):.1f} MB) exceeds maximum allowed "
                f"limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f} MB."
            )

        is_valid, error_msg = validate_pdf_bytes(content)
        if not is_valid:
            raise ValueError(f"Invalid PDF file: {error_msg}")

        safe_filename = sanitize_filename(raw_filename)
        content_hash = hashlib.sha256(content).hexdigest()
        file_path = self.upload_dir / f"{document_id}.pdf"

        file_path.write_bytes(content)
        logger.info(f"Saved PDF {safe_filename} to {file_path} ({len(content)} bytes)")

        return file_path, safe_filename, len(content), content_hash

    def extract_text_and_metadata(
        self,
        file_path: Path,
    ) -> Tuple[List[Dict[str, any]], Dict[str, any]]:
        """
        Extracts text page-by-page preserving 1-indexed page numbers.
        Returns: (pages_data, metadata)
        pages_data: [{'page': 1, 'text': '...', 'char_count': 123}, ...]
        metadata: {'total_pages': 10, 'pages_with_text': 8, 'needs_ocr': False, ...}
        """
        pages_data = []
        doc_metadata = {}

        try:
            with fitz.open(file_path) as pdf:
                total_pages = len(pdf)
                doc_metadata = {
                    "total_pages": total_pages,
                    "title": pdf.metadata.get("title") or "",
                    "author": pdf.metadata.get("author") or "",
                    "subject": pdf.metadata.get("subject") or "",
                    "producer": pdf.metadata.get("producer") or "",
                }

                pages_with_text = 0

                for page_idx, page in enumerate(pdf, start=1):
                    text = page.get_text("text").strip()
                    if text:
                        pages_with_text += 1
                        pages_data.append({
                            "page": page_idx,
                            "text": text,
                            "char_count": len(text),
                        })
                    else:
                        pages_data.append({
                            "page": page_idx,
                            "text": "",
                            "char_count": 0,
                        })

                doc_metadata["pages_with_text"] = pages_with_text
                # If no pages have extractable text or less than 20% on multi-page docs, flag OCR
                needs_ocr = pages_with_text == 0 or (total_pages > 2 and pages_with_text / total_pages < 0.2)
                doc_metadata["needs_ocr"] = needs_ocr

                if needs_ocr and pages_with_text == 0:
                    logger.warning(f"PDF {file_path} has 0 extractable text pages. OCR is required.")

        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            raise RuntimeError(f"Could not read PDF contents: {e}")

        return pages_data, doc_metadata

    def get_page_text(self, file_path: Path, page_number: int) -> Tuple[str, int]:
        """Returns text of a specific page and total page count."""
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found at {file_path}")

        with fitz.open(file_path) as pdf:
            total_pages = len(pdf)
            if page_number < 1 or page_number > total_pages:
                raise IndexError(f"Page number {page_number} is out of bounds (1-{total_pages})")
            page = pdf[page_number - 1]
            return page.get_text("text").strip(), total_pages

    def cleanup_file(self, file_path: Path) -> None:
        """Safely removes an uploaded file from disk."""
        try:
            if file_path and file_path.exists():
                file_path.unlink(missing_ok=True)
                logger.info(f"Cleaned up file {file_path}")
        except Exception as e:
            logger.warning(f"Error cleaning up file {file_path}: {e}")


pdf_service = PDFService()

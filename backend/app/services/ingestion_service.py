from pathlib import Path
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.db.models import Document
from app.db.repositories.chunk_repository import chunk_repository
from app.db.repositories.document_repository import document_repository
from app.services.chunking_service import chunking_service
from app.services.embedding_service import embedding_service
from app.services.pdf_service import pdf_service


class IngestionService:
    """Manages full document ingestion: PDF validation, storage, text extraction, chunking, and embedding."""

    def ingest_pdf(
        self,
        db: Session,
        document_id: UUID,
        raw_filename: str,
        content: bytes,
        owner_id: Optional[str] = None,
    ) -> Document:
        """
        Executes complete ingestion pipeline.
        Creates Document record -> Extracts text -> Chunks -> Embeds -> Stores in DB.
        """
        file_path = None
        try:
            # Step 1: Validate file & save to disk
            file_path, safe_filename, file_size, content_hash = pdf_service.validate_and_save(
                document_id=document_id,
                raw_filename=raw_filename,
                content=content,
            )

            # Step 2: Create document record with status 'processing'
            doc = document_repository.create(
                db=db,
                document_id=document_id,
                filename=safe_filename,
                storage_path=str(file_path),
                content_hash=content_hash,
                file_size_bytes=file_size,
                status="processing",
                owner_id=owner_id,
            )

            # Step 3: Extract text page by page
            pages_data, doc_meta = pdf_service.extract_text_and_metadata(file_path)
            total_pages = doc_meta.get("total_pages", 0)
            pages_with_text = doc_meta.get("pages_with_text", 0)

            if pages_with_text == 0:
                document_repository.update_status(
                    db,
                    document_id=document_id,
                    status="failed",
                    error_message="No extractable text found in PDF. Scanned documents requiring OCR are not supported in this run.",
                    page_count=total_pages,
                )
                raise ValueError("No extractable text found in PDF. Scanned documents require OCR.")

            # Step 4: Chunk text preserving paragraph boundaries & page numbers
            chunks = chunking_service.chunk_pages(pages_data)
            if not chunks:
                document_repository.update_status(
                    db,
                    document_id=document_id,
                    status="failed",
                    error_message="Could not generate non-empty text chunks from document pages.",
                    page_count=total_pages,
                )
                raise ValueError("No text chunks generated from document.")

            # Step 5: Generate normalized embeddings
            embeddings = embedding_service.embed_chunks(chunks)

            # Step 6: Persist chunks and vectors to database
            chunk_repository.bulk_create(
                db=db,
                document_id=document_id,
                chunks_data=chunks,
                embeddings=embeddings,
            )

            # Step 7: Mark document completed
            doc = document_repository.update_status(
                db,
                document_id=document_id,
                status="completed",
                page_count=total_pages,
            )

            logger.info(
                f"Successfully ingested {safe_filename} ({document_id}): "
                f"{total_pages} pages, {len(chunks)} chunks, status=completed."
            )
            return doc

        except Exception as e:
            logger.error(f"Ingestion failed for {raw_filename} ({document_id}): {e}")
            # Ensure document status is set to failed if record exists
            try:
                document_repository.update_status(
                    db,
                    document_id=document_id,
                    status="failed",
                    error_message=str(e),
                )
            except Exception:
                pass
            raise


ingestion_service = IngestionService()

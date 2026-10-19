from pathlib import Path
from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import settings
from app.core.logging import logger
from app.db.repositories.document_repository import document_repository
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentResponse,
    DocumentUploadResponse,
    PageResponse,
)
from app.services.ingestion_service import ingestion_service
from app.services.pdf_service import pdf_service

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a PDF document",
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Validates uploaded PDF, creates a Document entity, extracts text,
    splits into chunks, computes embeddings, and persists to pgvector.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported (.pdf).",
        )

    # Read content up to max size + 1 to detect oversized files safely
    content = await file.read(settings.MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.0f} MB.",
        )

    document_id = uuid4()

    try:
        doc = ingestion_service.ingest_pdf(
            db=db,
            document_id=document_id,
            raw_filename=file.filename,
            content=content,
        )

        return DocumentUploadResponse(
            document_id=doc.id,
            filename=doc.filename,
            processing_status=doc.processing_status,
            message="Document uploaded and indexed successfully.",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}",
        )


@router.get("", response_model=List[DocumentResponse], summary="List all indexed documents")
def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return document_repository.list_all(db, skip=skip, limit=limit)


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details by ID",
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    doc = document_repository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )

    chunk_count = document_repository.count_chunks(db, document_id)

    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        page_count=doc.page_count,
        file_size_bytes=doc.file_size_bytes,
        processing_status=doc.processing_status,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        total_chunks=chunk_count,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its stored chunks",
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    doc = document_repository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )

    storage_path = Path(doc.storage_path)
    # Remove from database (cascades to chunks)
    deleted = document_repository.delete(db, document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from database.",
        )

    # Clean up file on disk
    pdf_service.cleanup_file(storage_path)
    return None


@router.get(
    "/{document_id}/pages/{page_number}",
    response_model=PageResponse,
    summary="Get extracted text for a specific document page",
)
def get_document_page(
    document_id: UUID,
    page_number: int,
    db: Session = Depends(get_db),
):
    doc = document_repository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found.",
        )

    storage_path = Path(doc.storage_path)
    try:
        page_text, total_pages = pdf_service.get_page_text(storage_path, page_number)
        return PageResponse(
            document_id=doc.id,
            page_number=page_number,
            text=page_text,
            total_pages=total_pages,
            has_text=bool(page_text.strip()),
        )
    except IndexError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read page text: {str(e)}",
        )


@router.get(
    "/{document_id}/file",
    summary="Serve the raw PDF file for in-browser viewer",
)
def get_document_file(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    doc = document_repository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    file_path = Path(doc.storage_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Underlying PDF file was not found on disk.",
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=doc.filename,
    )

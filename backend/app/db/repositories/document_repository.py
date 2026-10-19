from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentChunk


class DocumentRepository:
    """Repository handling database operations for Document entities."""

    def create(
        self,
        db: Session,
        document_id: UUID,
        filename: str,
        storage_path: str,
        content_hash: str,
        file_size_bytes: int,
        page_count: int = 0,
        status: str = "queued",
        owner_id: Optional[str] = None,
    ) -> Document:
        doc = Document(
            id=document_id,
            filename=filename,
            storage_path=storage_path,
            content_hash=content_hash,
            file_size_bytes=file_size_bytes,
            page_count=page_count,
            processing_status=status,
            owner_id=owner_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc

    def get_by_id(self, db: Session, document_id: UUID) -> Optional[Document]:
        return db.get(Document, document_id)

    def get_by_hash(self, db: Session, content_hash: str) -> Optional[Document]:
        stmt = select(Document).where(Document.content_hash == content_hash)
        return db.execute(stmt).scalars().first()

    def list_all(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        owner_id: Optional[str] = None,
    ) -> List[Document]:
        stmt = select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        if owner_id:
            stmt = stmt.where(Document.owner_id == owner_id)
        return list(db.execute(stmt).scalars().all())

    def update_status(
        self,
        db: Session,
        document_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        page_count: Optional[int] = None,
    ) -> Optional[Document]:
        doc = self.get_by_id(db, document_id)
        if not doc:
            return None
        doc.processing_status = status
        if error_message is not None:
            doc.error_message = error_message
        if page_count is not None:
            doc.page_count = page_count
        db.commit()
        db.refresh(doc)
        return doc

    def delete(self, db: Session, document_id: UUID) -> bool:
        doc = self.get_by_id(db, document_id)
        if not doc:
            return False
        db.delete(doc)
        db.commit()
        return True

    def count_chunks(self, db: Session, document_id: UUID) -> int:
        stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.document_id == document_id)
        return db.execute(stmt).scalar() or 0


document_repository = DocumentRepository()

import uuid
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID
import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentChunk


class ChunkRepository:
    """Repository handling persistence, vector similarity search, and keyword search on chunks."""

    def bulk_create(
        self,
        db: Session,
        document_id: UUID,
        chunks_data: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> int:
        """Persists document chunks and their corresponding embedding vectors transactionally."""
        if not chunks_data:
            return 0

        chunk_objects = []
        for i, chunk in enumerate(chunks_data):
            emb = embeddings[i] if i < len(embeddings) else None
            chunk_obj = DocumentChunk(
                id=uuid.uuid4(),
                document_id=document_id,
                chunk_index=chunk["chunk_index"],
                page_number=chunk["page_number"],
                chunk_text=chunk["chunk_text"],
                embedding=emb,
                metadata_json=chunk.get("metadata", {}),
            )
            chunk_objects.append(chunk_obj)

        db.add_all(chunk_objects)
        db.commit()
        return len(chunk_objects)

    def get_by_document(self, db: Session, document_id: UUID) -> List[DocumentChunk]:
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(db.execute(stmt).scalars().all())

    def vector_search(
        self,
        db: Session,
        query_embedding: List[float],
        top_k: int = 20,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Performs dense vector similarity search.
        Uses pgvector cosine distance on PostgreSQL, and vector dot-product on SQLite fallback.
        Returns: list of (DocumentChunk, similarity_score) ordered by highest similarity.
        """
        bind = db.get_bind()
        if bind.dialect.name == "postgresql":
            dist_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")
            stmt = (
                select(DocumentChunk, (1.0 - dist_expr).label("similarity"))
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.embedding.is_not(None))
                .where(Document.processing_status == "completed")
            )

            if document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

            stmt = stmt.order_by(dist_expr.asc()).limit(top_k)
            results = db.execute(stmt).all()
            return [(row[0], float(row[1])) for row in results]
        else:
            # SQLite fallback: in-memory cosine similarity via numpy
            stmt = (
                select(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(DocumentChunk.embedding.is_not(None))
                .where(Document.processing_status == "completed")
            )
            if document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
            chunks = list(db.execute(stmt).scalars().all())
            if not chunks:
                return []

            q_vec = np.array(query_embedding, dtype=np.float32)
            scored = []
            for c in chunks:
                if c.embedding:
                    c_vec = np.array(c.embedding, dtype=np.float32)
                    sim = float(np.dot(c_vec, q_vec))
                    scored.append((c, sim))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

    def keyword_search(
        self,
        db: Session,
        query_text: str,
        top_k: int = 20,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Performs full-text keyword search using PostgreSQL tsvector on Postgres,
        or token substring matching on SQLite.
        Returns: list of (DocumentChunk, rank_score) ordered by highest rank.
        """
        clean_query = query_text.strip()
        if not clean_query:
            return []

        bind = db.get_bind()
        if bind.dialect.name == "postgresql":
            ts_query = func.websearch_to_tsquery("english", clean_query)
            ts_vector = func.to_tsvector("english", DocumentChunk.chunk_text)
            rank_expr = func.ts_rank_cd(ts_vector, ts_query).label("rank")

            stmt = (
                select(DocumentChunk, rank_expr)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(ts_vector.op("@@")(ts_query))
                .where(Document.processing_status == "completed")
            )

            if document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))

            stmt = stmt.order_by(rank_expr.desc()).limit(top_k)
            results = db.execute(stmt).all()
            return [(row[0], float(row[1])) for row in results]
        else:
            # SQLite fallback: keyword occurrence matching
            tokens = [w.lower() for w in clean_query.split() if len(w) > 2]
            stmt = (
                select(DocumentChunk)
                .join(Document, DocumentChunk.document_id == Document.id)
                .where(Document.processing_status == "completed")
            )
            if document_ids:
                stmt = stmt.where(DocumentChunk.document_id.in_(document_ids))
            chunks = list(db.execute(stmt).scalars().all())

            scored = []
            for c in chunks:
                text_lower = c.chunk_text.lower()
                matches = sum(1 for t in tokens if t in text_lower)
                if matches > 0:
                    scored.append((c, float(matches)))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]


chunk_repository = ChunkRepository()

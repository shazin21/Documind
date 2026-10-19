from collections import defaultdict
from typing import Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.repositories.chunk_repository import chunk_repository
from app.rag.types import ScoredPassage
from app.services.embedding_service import embedding_service


class RetrievalService:
    """Orchestrates dense, keyword, and hybrid retrieval with Reciprocal Rank Fusion (RRF)."""

    def __init__(self, rrf_k: int = 60):
        self.rrf_k = rrf_k

    def retrieve(
        self,
        db: Session,
        query: str,
        top_k: int = 5,
        mode: str = "hybrid",  # "hybrid", "dense", "keyword"
        document_ids: Optional[List[UUID]] = None,
        candidate_pool: int = 20,
    ) -> List[ScoredPassage]:
        """
        Retrieves top passages for a user query using dense vector search,
        keyword search, or hybrid RRF fusion.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        if mode == "dense":
            return self._dense_search(db, clean_query, top_k, document_ids)
        elif mode == "keyword":
            return self._keyword_search(db, clean_query, top_k, document_ids)
        else:
            return self._hybrid_search(db, clean_query, top_k, document_ids, candidate_pool)

    def _dense_search(
        self,
        db: Session,
        query: str,
        top_k: int,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[ScoredPassage]:
        query_embedding = embedding_service.embed_query(query)
        dense_results = chunk_repository.vector_search(
            db,
            query_embedding=query_embedding,
            top_k=top_k,
            document_ids=document_ids,
        )
        passages = []
        for rank, (chunk, score) in enumerate(dense_results, start=1):
            doc_name = chunk.document.filename if chunk.document else "Unknown"
            passages.append(
                ScoredPassage(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=doc_name,
                    page_number=chunk.page_number,
                    text=chunk.chunk_text,
                    score=score,
                    rank=rank,
                    source_retriever="dense",
                    metadata=chunk.metadata_json,
                )
            )
        return passages

    def _keyword_search(
        self,
        db: Session,
        query: str,
        top_k: int,
        document_ids: Optional[List[UUID]] = None,
    ) -> List[ScoredPassage]:
        keyword_results = chunk_repository.keyword_search(
            db,
            query_text=query,
            top_k=top_k,
            document_ids=document_ids,
        )
        passages = []
        for rank, (chunk, score) in enumerate(keyword_results, start=1):
            doc_name = chunk.document.filename if chunk.document else "Unknown"
            passages.append(
                ScoredPassage(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=doc_name,
                    page_number=chunk.page_number,
                    text=chunk.chunk_text,
                    score=score,
                    rank=rank,
                    source_retriever="keyword",
                    metadata=chunk.metadata_json,
                )
            )
        return passages

    def _hybrid_search(
        self,
        db: Session,
        query: str,
        top_k: int,
        document_ids: Optional[List[UUID]] = None,
        candidate_pool: int = 20,
    ) -> List[ScoredPassage]:
        """Executes dense + keyword search and merges rankings using Reciprocal Rank Fusion."""
        # 1. Dense retrieval
        query_embedding = embedding_service.embed_query(query)
        dense_candidates = chunk_repository.vector_search(
            db,
            query_embedding=query_embedding,
            top_k=candidate_pool,
            document_ids=document_ids,
        )

        # 2. Keyword retrieval
        keyword_candidates = chunk_repository.keyword_search(
            db,
            query_text=query,
            top_k=candidate_pool,
            document_ids=document_ids,
        )

        # 3. Reciprocal Rank Fusion calculation
        rrf_scores: Dict[UUID, float] = defaultdict(float)
        chunk_map: Dict[UUID, any] = {}

        for rank, (chunk, _) in enumerate(dense_candidates, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] += 1.0 / (self.rrf_k + rank)

        for rank, (chunk, _) in enumerate(keyword_candidates, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] += 1.0 / (self.rrf_k + rank)

        # Sort chunk IDs by descending RRF score
        sorted_chunk_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)[
            :top_k
        ]

        fused_passages: List[ScoredPassage] = []
        for rank, chunk_id in enumerate(sorted_chunk_ids, start=1):
            chunk = chunk_map[chunk_id]
            doc_name = chunk.document.filename if chunk.document else "Unknown"
            fused_passages.append(
                ScoredPassage(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=doc_name,
                    page_number=chunk.page_number,
                    text=chunk.chunk_text,
                    score=round(rrf_scores[chunk_id], 4),
                    rank=rank,
                    source_retriever="hybrid_rrf",
                    metadata=chunk.metadata_json,
                )
            )

        logger.info(
            f"Hybrid retrieval fetched {len(dense_candidates)} dense, "
            f"{len(keyword_candidates)} keyword candidates -> {len(fused_passages)} fused."
        )
        return fused_passages


retrieval_service = RetrievalService()

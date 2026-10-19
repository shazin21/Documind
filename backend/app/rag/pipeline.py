from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.rag.types import RAGResult, ScoredPassage
from app.services.generation_service import generation_service
from app.services.reranking_service import reranking_service
from app.services.retrieval_service import retrieval_service


class RAGPipeline:
    """End-to-end deterministic RAG execution pipeline."""

    def execute(
        self,
        db: Session,
        question: str,
        top_k: int = 5,
        document_ids: Optional[List[UUID]] = None,
        use_reranker: bool = False,
        retrieval_mode: str = "hybrid",
    ) -> RAGResult:
        """
        Runs full pipeline:
        1. Retrieval (dense/keyword/hybrid RRF)
        2. Optional Cross-Encoder reranking
        3. Grounded generation & citation verification
        """
        logger.info(
            f"Executing RAG pipeline: mode={retrieval_mode}, top_k={top_k}, "
            f"use_reranker={use_reranker}, doc_filters={len(document_ids) if document_ids else 'ALL'}"
        )

        candidate_pool = settings.RERANK_CANDIDATE_POOL if use_reranker else top_k

        # Stage 1: Retrieval
        passages: List[ScoredPassage] = retrieval_service.retrieve(
            db=db,
            query=question,
            top_k=candidate_pool,
            mode=retrieval_mode,
            document_ids=document_ids,
            candidate_pool=candidate_pool,
        )

        # Stage 2: Optional Reranking
        if use_reranker and passages:
            passages = reranking_service.rerank(
                query=question,
                passages=passages,
                top_k=top_k,
            )
        else:
            passages = passages[:top_k]

        # Stage 3: Grounded Answer Generation & Citation Extraction
        result = generation_service.generate_grounded_answer(
            question=question,
            passages=passages,
        )

        return result


rag_pipeline = RAGPipeline()

import time
from typing import List, Optional
from app.core.logging import logger
from app.providers.llm import BaseLLMProvider, get_llm_provider
from app.rag.prompts import SYSTEM_GROUNDED_QA_PROMPT, build_grounded_qa_prompt
from app.rag.types import RAGResult, ScoredPassage
from app.schemas.chat import EvidenceItem
from app.services.citation_service import citation_service


class GenerationService:
    """Manages grounded answer generation, citation extraction, and insufficient evidence handling."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self._provider = llm_provider

    @property
    def provider(self) -> BaseLLMProvider:
        if self._provider is None:
            self._provider = get_llm_provider()
        return self._provider

    def generate_grounded_answer(
        self,
        question: str,
        passages: List[ScoredPassage],
    ) -> RAGResult:
        """Executes prompt building, LLM inference, citation extraction, and abstention checks."""
        start_time = time.perf_counter()

        # If no passages were retrieved at all, return insufficient evidence immediately
        if not passages:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return RAGResult(
                answer="Based on the provided documents, there is insufficient evidence to answer this question.",
                citations=[],
                evidence=[],
                insufficient_evidence=True,
                latency_ms=latency_ms,
            )

        prompt = build_grounded_qa_prompt(question, passages)

        try:
            raw_answer = self.provider.generate(
                prompt=prompt,
                system_prompt=SYSTEM_GROUNDED_QA_PROMPT,
            )
            raw_answer = raw_answer.replace("【", "[").replace("】", "]")
        except Exception as e:
            logger.error(f"Generation error: {e}")
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return RAGResult(
                answer=f"Error generating answer: {str(e)}",
                citations=[],
                evidence=[],
                insufficient_evidence=True,
                latency_ms=latency_ms,
            )

        # Check for insufficient evidence triggers
        insufficient_markers = [
            "insufficient evidence",
            "not mentioned in the provided",
            "cannot be answered from the",
            "does not contain enough information",
            "no relevant information",
        ]
        is_insufficient = any(marker in raw_answer.lower() for marker in insufficient_markers)

        # Extract and verify citations
        citations = []
        if not is_insufficient:
            citations = citation_service.extract_and_verify_citations(raw_answer, passages)

        # Convert passages to UI EvidenceItems
        evidence_items = [
            EvidenceItem(
                chunk_id=p.chunk_id,
                document_id=p.document_id,
                document_name=p.document_name,
                page_number=p.page_number,
                chunk_text=p.text,
                score=p.score,
                rank=p.rank,
                retrieval_type=p.source_retriever,
            )
            for p in passages
        ]

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return RAGResult(
            answer=raw_answer,
            citations=citations,
            evidence=evidence_items,
            insufficient_evidence=is_insufficient,
            latency_ms=latency_ms,
        )


generation_service = GenerationService()

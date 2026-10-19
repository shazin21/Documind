from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID
from app.schemas.chat import Citation, EvidenceItem


@dataclass
class ScoredPassage:
    """Represents a passage retrieved from the vector or keyword store with scoring metadata."""

    chunk_id: UUID
    document_id: UUID
    document_name: str
    page_number: int
    text: str
    score: float
    rank: int = 1
    source_retriever: str = "dense"  # "dense", "keyword", "rrf", "rerank"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGContext:
    """Constructed context ready for LLM generation."""

    passages: List[ScoredPassage]
    formatted_context_str: str
    total_characters: int


@dataclass
class RAGResult:
    """End-to-end result of retrieval, grounded generation, and citation verification."""

    answer: str
    citations: List[Citation]
    evidence: List[EvidenceItem]
    insufficient_evidence: bool
    latency_ms: float

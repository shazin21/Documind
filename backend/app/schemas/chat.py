from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    citation_id: str = Field(..., description="Unique citation key e.g. [1]")
    document_id: UUID
    document_name: str
    page_number: int
    chunk_id: UUID
    excerpt: str = Field(..., description="Direct verbatim excerpt from the document")
    score: float = Field(0.0, description="Relevance score")


class EvidenceItem(BaseModel):
    chunk_id: UUID
    document_id: UUID
    document_name: str
    page_number: int
    chunk_text: str
    score: float
    rank: int
    retrieval_type: str = Field(..., description="'dense', 'keyword', or 'fused'")


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    document_ids: Optional[List[UUID]] = Field(
        default=None,
        description="Filter retrieval to specific documents. None means search across all documents.",
    )
    conversation_id: Optional[UUID] = None
    use_reranker: bool = False
    top_k: int = Field(5, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    conversation_id: UUID
    message_id: UUID
    insufficient_evidence: bool = False
    latency_ms: float = 0.0


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    citations_json: List[dict] = Field(default_factory=list)
    insufficient_evidence: bool = False
    latency_ms: Optional[float] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

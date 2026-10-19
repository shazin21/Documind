from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PageText(BaseModel):
    page: int = Field(..., ge=1, description="1-indexed page number")
    text: str = Field(..., description="Extracted text from page")


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    page_number: int
    chunk_text: str
    metadata_json: dict = Field(default_factory=dict)


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    page_count: int
    file_size_bytes: int
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    total_chunks: int = 0


class DocumentUploadResponse(BaseModel):
    document_id: UUID
    filename: str
    processing_status: str
    message: str


class PageResponse(BaseModel):
    document_id: UUID
    page_number: int
    text: str
    total_pages: int
    has_text: bool

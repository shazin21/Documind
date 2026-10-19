from typing import List
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.logging import logger
from app.db.repositories.conversation_repository import conversation_repository
from app.rag.pipeline import rag_pipeline
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    MessageResponse,
)

router = APIRouter(tags=["Chat"])


@router.post(
    "/api/v1/chat",
    response_model=ChatResponse,
    summary="Ask a question and receive a grounded answer with citations",
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Executes grounded retrieval-augmented generation.
    Retrieves relevant passages, performs grounded generation, verifies citations,
    and records the conversation history.
    """
    # 1. Resolve or create conversation
    conv_id = request.conversation_id or uuid4()
    conv = conversation_repository.get_conversation(db, conv_id)
    if not conv:
        conv = conversation_repository.create_conversation(
            db=db,
            conversation_id=conv_id,
            title="New Conversation",
        )

    # 2. Record user question message
    user_msg_id = uuid4()
    conversation_repository.add_message(
        db=db,
        conversation_id=conv.id,
        role="user",
        content=request.question,
        message_id=user_msg_id,
    )

    # 3. Execute RAG pipeline
    rag_result = rag_pipeline.execute(
        db=db,
        question=request.question,
        top_k=request.top_k,
        document_ids=request.document_ids,
        use_reranker=request.use_reranker,
        retrieval_mode="hybrid",
    )

    # 4. Record assistant message with citations and latency
    assistant_msg_id = uuid4()
    citations_data = [c.model_dump(mode="json") for c in rag_result.citations]

    conversation_repository.add_message(
        db=db,
        conversation_id=conv.id,
        role="assistant",
        content=rag_result.answer,
        citations_json=citations_data,
        insufficient_evidence=rag_result.insufficient_evidence,
        latency_ms=rag_result.latency_ms,
        message_id=assistant_msg_id,
    )

    return ChatResponse(
        answer=rag_result.answer,
        citations=rag_result.citations,
        evidence=rag_result.evidence,
        conversation_id=conv.id,
        message_id=assistant_msg_id,
        insufficient_evidence=rag_result.insufficient_evidence,
        latency_ms=rag_result.latency_ms,
    )


@router.get(
    "/api/v1/conversations",
    response_model=List[ConversationResponse],
    summary="List all conversations",
)
def list_conversations(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    convs = conversation_repository.list_conversations(db, limit=limit)
    response = []
    for c in convs:
        msg_count = conversation_repository.count_messages(db, c.id)
        response.append(
            ConversationResponse(
                id=c.id,
                title=c.title,
                created_at=c.created_at,
                updated_at=c.updated_at,
                message_count=msg_count,
            )
        )
    return response


@router.get(
    "/api/v1/conversations/{conversation_id}",
    response_model=List[MessageResponse],
    summary="Get all messages in a conversation",
)
def get_conversation_messages(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):
    conv = conversation_repository.get_conversation(db, conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found.",
        )
    return conversation_repository.get_messages(db, conversation_id)

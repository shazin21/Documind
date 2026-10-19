import uuid
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.db.models import Conversation, Message


class ConversationRepository:
    """Repository handling conversations and chat history messages."""

    def create_conversation(
        self,
        db: Session,
        title: str = "New Conversation",
        conversation_id: Optional[UUID] = None,
    ) -> Conversation:
        conv = Conversation(
            id=conversation_id or uuid.uuid4(),
            title=title,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    def get_conversation(self, db: Session, conversation_id: UUID) -> Optional[Conversation]:
        return db.get(Conversation, conversation_id)

    def list_conversations(self, db: Session, limit: int = 50) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        return list(db.execute(stmt).scalars().all())

    def count_messages(self, db: Session, conversation_id: UUID) -> int:
        stmt = select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
        return db.execute(stmt).scalar() or 0

    def add_message(
        self,
        db: Session,
        conversation_id: UUID,
        role: str,
        content: str,
        citations_json: Optional[list] = None,
        insufficient_evidence: bool = False,
        latency_ms: Optional[float] = None,
        message_id: Optional[UUID] = None,
    ) -> Message:
        msg = Message(
            id=message_id or uuid.uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations_json=citations_json or [],
            insufficient_evidence=insufficient_evidence,
            latency_ms=latency_ms,
        )
        db.add(msg)
        # Update conversation timestamp and title if first user message
        conv = self.get_conversation(db, conversation_id)
        if conv and role == "user" and conv.title == "New Conversation":
            # Set title to first 40 chars of question
            clean_title = content.strip().split("\n")[0][:45]
            conv.title = clean_title or "Conversation"

        db.commit()
        db.refresh(msg)
        return msg

    def get_messages(self, db: Session, conversation_id: UUID) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(db.execute(stmt).scalars().all())


conversation_repository = ConversationRepository()

"""
Modèles SQLAlchemy — Coach IA SOMA (LOT 9).

Tables :
  - conversation_threads  : fils de conversation utilisateur ↔ coach
  - conversation_messages : messages individuels (user / coach)
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class ConversationThread(Base, UUIDMixin, TimestampMixin):
    """Fil de conversation entre l'utilisateur et SOMA Coach."""

    __tablename__ = "conversation_threads"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[Optional[str]] = mapped_column(String(200))
    # Résumé court de la conversation (généré par le coach après N messages)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    # Métadonnées libres (mode session, contexte, etc.)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}"
    )


class ConversationMessage(Base, UUIDMixin):
    """Message individuel dans un fil de conversation."""

    __tablename__ = "conversation_messages"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversation_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role: Mapped[str] = mapped_column(String(10), nullable=False)
    # "user" | "coach"

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Métadonnées coach : confidence, reasoning, model_used, context_tokens, etc.
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, default=dict, server_default="{}"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

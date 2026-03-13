"""
Schémas Pydantic v2 — Coach IA SOMA (LOT 9).

Valident les requêtes et sérialisent les réponses des endpoints coach.
"""
from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, Field


# ── Requêtes ─────────────────────────────────────────────────────────────────

class AskCoachRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Question posée au coach SOMA.",
        examples=["Pourquoi suis-je aussi fatigué aujourd'hui ?"],
    )
    thread_id: Optional[uuid.UUID] = Field(
        None,
        description="ID du fil de conversation existant (None = nouveau thread).",
    )


class CreateThreadRequest(BaseModel):
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Titre optionnel du fil de conversation.",
    )


# ── Réponses ─────────────────────────────────────────────────────────────────

class CoachAnswerResponse(BaseModel):
    """Réponse structurée du coach IA."""
    summary: str = Field(..., description="Synthèse courte (1-2 phrases).")
    full_response: str = Field(..., description="Réponse complète en Markdown.")
    recommendations: list[str] = Field(
        default_factory=list,
        description="Liste de recommandations concrètes.",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Alertes ou points de vigilance.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de confiance (0-1) basé sur la disponibilité des données.",
    )
    context_tokens_estimate: int = Field(0, description="Estimation du nb de tokens de contexte.")
    model_used: str = Field(..., description="Modèle IA utilisé ou 'mock'.")
    thread_id: uuid.UUID = Field(..., description="ID du fil de conversation.")
    message_id: uuid.UUID = Field(..., description="ID du message coach créé.")


class ConversationThreadResponse(BaseModel):
    """Représentation d'un fil de conversation."""
    id: uuid.UUID
    title: Optional[str]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageResponse(BaseModel):
    """Représentation d'un message dans une conversation."""
    id: uuid.UUID
    thread_id: uuid.UUID
    role: str  # "user" | "coach"
    content: str
    created_at: datetime
    metadata: Optional[dict] = Field(None, alias="metadata_")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ConversationThreadDetailResponse(BaseModel):
    """Fil de conversation avec ses messages."""
    thread: ConversationThreadResponse
    messages: list[ConversationMessageResponse]


class ThreadListResponse(BaseModel):
    """Liste des fils de conversation."""
    threads: list[ConversationThreadResponse]
    total: int


# ── Quick Advice (LOT 18) — réponse rapide sans persistence ──────────────────

class QuickAdviceRequest(BaseModel):
    """Requête conseil rapide — pas de thread, pas de persistence."""
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Question courte posée au coach SOMA.",
        examples=["Dois-je m'entraîner aujourd'hui ?"],
    )


class QuickAdviceResponse(BaseModel):
    """Réponse synthétique du coach — 3 phrases max, sans persistence DB."""
    answer: str = Field(..., description="Réponse principale (2 phrases max).")
    recommendations: list[str] = Field(
        default_factory=list,
        max_length=2,
        description="2 actions concrètes max.",
    )
    alert: Optional[str] = Field(
        None,
        description="1 alerte critique si nécessaire, sinon None.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Score de confiance basé sur la disponibilité des données.",
    )
    model_used: str = Field(..., description="Modèle IA utilisé ou 'mock'.")
    context_summary: str = Field(
        ...,
        description="Résumé compact du contexte utilisé (ex: readiness: 72%, fatigue: 45%).",
    )

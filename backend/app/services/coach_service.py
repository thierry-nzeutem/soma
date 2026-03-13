"""
Coach Service — SOMA LOT 9.

Orchestre le flow complet :
  1. Assembler le contexte (context_builder)
  2. Récupérer l'historique de conversation
  3. Appeler Claude (claude_client)
  4. Persister les messages
  5. Retourner un CoachAnswer structuré

Fonctions principales :
  ask_coach()      → CoachAnswer (réponse complète)
  create_thread()  → ConversationThread
  get_threads()    → list[ConversationThread]
  get_messages()   → list[ConversationMessage]
"""
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coach import ConversationMessage, ConversationThread
from app.models.user import UserProfile
from app.services.claude_client import generate_coach_reply
from app.services.context_builder import build_coach_context

logger = logging.getLogger(__name__)


# ── Réponse structurée ────────────────────────────────────────────────────────

@dataclass
class CoachAnswer:
    """Réponse structurée du coach IA."""
    summary: str
    full_response: str
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    confidence: float = 0.75
    context_tokens_estimate: int = 0
    model_used: str = "mock"
    thread_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None


# ── Parsing de la réponse ─────────────────────────────────────────────────────

def _parse_coach_reply(raw: str) -> tuple[str, list[str], list[str]]:
    """
    Extrait summary, recommendations et warnings du texte brut du coach.
    Structure attendue (markdown) :
      **Synthèse** : ...
      **Points clés** : - ...
      **Recommandations** : - ...
      ⚠ Vigilance : ...
    """
    # Synthèse : première phrase après "Synthèse"
    summary = raw
    synth_match = re.search(r'\*\*Synthèse\*\*\s*:?\s*(.+?)(?:\n|$)', raw, re.IGNORECASE)
    if synth_match:
        summary = synth_match.group(1).strip()

    # Recommandations : bullet points après "Recommandations"
    recs: list[str] = []
    recs_match = re.search(
        r'\*\*Recommandations?\*\*.*?\n(.*?)(?:\n\*\*|⚠|\Z)',
        raw, re.DOTALL | re.IGNORECASE,
    )
    if recs_match:
        block = recs_match.group(1)
        recs = [
            line.lstrip("•·-* ").strip()
            for line in block.split("\n")
            if line.strip() and line.strip() not in ("", "\n")
        ]

    # Warnings : lignes avec ⚠
    warnings: list[str] = [
        line.strip().lstrip("⚠ ").strip()
        for line in raw.split("\n")
        if "⚠" in line and line.strip()
    ]

    return summary, recs, warnings


# ── Fonctions principales ──────────────────────────────────────────────────────

async def create_thread(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: Optional[str] = None,
) -> ConversationThread:
    """Crée un nouveau fil de conversation."""
    thread = ConversationThread(
        user_id=user_id,
        title=title or "Nouvelle conversation",
    )
    db.add(thread)
    await db.flush()
    logger.info("Thread créé : %s pour user %s", thread.id, user_id)
    return thread


async def get_threads(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[ConversationThread]:
    """Liste les fils de conversation de l'utilisateur (du plus récent)."""
    result = await db.execute(
        select(ConversationThread)
        .where(ConversationThread.user_id == user_id)
        .order_by(ConversationThread.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_messages(
    db: AsyncSession,
    thread_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[ConversationMessage]:
    """Messages d'un fil (vérifie la propriété)."""
    # Vérifier que le thread appartient à l'utilisateur
    thread_res = await db.execute(
        select(ConversationThread).where(
            and_(
                ConversationThread.id == thread_id,
                ConversationThread.user_id == user_id,
            )
        )
    )
    if thread_res.scalar_one_or_none() is None:
        raise PermissionError(f"Thread {thread_id} introuvable ou accès refusé")

    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.thread_id == thread_id)
        .order_by(ConversationMessage.created_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def ask_coach(
    db: AsyncSession,
    user_id: uuid.UUID,
    question: str,
    thread_id: Optional[uuid.UUID] = None,
    target_date: Optional[date] = None,
) -> CoachAnswer:
    """
    Flow complet : contexte → Claude → réponse structurée + persistance.

    Si thread_id est None, un nouveau thread est créé.
    """
    target_date = target_date or date.today()

    # ── Profil utilisateur ────────────────────────────────────────────────
    prof_res = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = prof_res.scalar_one_or_none()

    # ── Contexte physiologique ────────────────────────────────────────────
    coach_ctx = await build_coach_context(db, user_id, profile, target_date)
    context_text = coach_ctx.to_prompt_text()

    # ── Thread ────────────────────────────────────────────────────────────
    if thread_id is None:
        thread = await create_thread(db, user_id, title=question[:80])
        thread_id = thread.id
    else:
        thread_res = await db.execute(
            select(ConversationThread).where(
                and_(
                    ConversationThread.id == thread_id,
                    ConversationThread.user_id == user_id,
                )
            )
        )
        thread = thread_res.scalar_one_or_none()
        if thread is None:
            raise PermissionError(f"Thread {thread_id} introuvable ou accès refusé")

    # ── Historique de conversation (pour la continuité) ───────────────────
    hist_res = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.thread_id == thread_id)
        .order_by(ConversationMessage.created_at.asc())
        .limit(10)
    )
    history_msgs = hist_res.scalars().all()
    conversation_history = [
        {"role": msg.role if msg.role == "user" else "assistant",
         "content": msg.content}
        for msg in history_msgs
    ]

    # ── Persister la question utilisateur ─────────────────────────────────
    user_msg = ConversationMessage(
        thread_id=thread_id,
        role="user",
        content=question,
        metadata_={"context_chars": len(context_text)},
    )
    db.add(user_msg)
    await db.flush()

    # ── Appel au coach ────────────────────────────────────────────────────
    from app.core.config import settings
    raw_reply = await generate_coach_reply(
        question=question,
        context_text=context_text,
        conversation_history=conversation_history,
    )

    # ── Parsing ───────────────────────────────────────────────────────────
    summary, recommendations, warnings = _parse_coach_reply(raw_reply)

    # Confiance basée sur la confiance du metabolic twin
    confidence = 0.75
    if coach_ctx.metabolic:
        confidence = max(0.5, coach_ctx.metabolic.confidence_score)

    # ── Persister la réponse du coach ─────────────────────────────────────
    coach_msg = ConversationMessage(
        thread_id=thread_id,
        role="coach",
        content=raw_reply,
        metadata_={
            "model_used": settings.CLAUDE_COACH_MODEL,
            "confidence": confidence,
            "context_chars": len(context_text),
            "mock_mode": settings.CLAUDE_COACH_MOCK_MODE,
        },
    )
    db.add(coach_msg)
    await db.flush()

    logger.info(
        "Coach réponse pour user %s thread %s (confiance %.0f%%)",
        user_id, thread_id, confidence * 100,
    )

    return CoachAnswer(
        summary=summary,
        full_response=raw_reply,
        recommendations=recommendations,
        warnings=warnings,
        confidence=round(confidence, 2),
        context_tokens_estimate=len(context_text) // 4,
        model_used=(
            "mock" if settings.CLAUDE_COACH_MOCK_MODE else settings.CLAUDE_COACH_MODEL
        ),
        thread_id=thread_id,
        message_id=coach_msg.id,
    )

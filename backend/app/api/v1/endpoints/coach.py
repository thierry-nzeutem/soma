"""
Endpoints Coach IA — SOMA LOT 9 + LOT 18.

Routes :
  POST /coach/ask             → Poser une question au coach (avec persistence)
  POST /coach/quick-advice    → Conseil rapide sans persistence (LOT 18)
  POST /coach/thread          → Créer un nouveau fil de conversation
  GET  /coach/history         → Lister les fils de l'utilisateur
  GET  /coach/history/{id}    → Détail d'un fil avec ses messages
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.entitlements import require_feature
from app.core.features import FeatureCode
from app.db.session import get_db
from app.models.user import User
from app.schemas.coach import (
    AskCoachRequest,
    CoachAnswerResponse,
    ConversationThreadDetailResponse,
    ConversationThreadResponse,
    ConversationMessageResponse,
    CreateThreadRequest,
    ThreadListResponse,
    QuickAdviceRequest,
    QuickAdviceResponse,
)
from app.services.coach_service import (
    ask_coach,
    create_thread,
    get_messages,
    get_threads,
)

logger = logging.getLogger(__name__)

coach_router = APIRouter(prefix="/coach", tags=["Coach IA"])

# Prompt système pour le conseil rapide (LOT 18)
_QUICK_ADVICE_SYSTEM = (
    "Tu es SOMA, coach santé IA personnel. "
    "Réponds en 3 phrases maximum, de façon directe et actionnelle. "
    "Format STRICT (respecte exactement ces balises) :\n"
    "**Réponse**: [2 phrases max basées sur les données]\n"
    "**À faire**: [2 actions concrètes max, une par ligne, avec tiret]\n"
    "**Alerte**: [1 alerte critique si nécessaire, sinon omets cette ligne]"
)


def _parse_quick_reply(raw: str) -> tuple[str, list[str], Optional[str]]:
    """Parse la réponse quick-advice en (answer, recommendations, alert)."""
    import re

    answer = ""
    recs: list[str] = []
    alert: Optional[str] = None

    # Réponse principale
    m = re.search(r"\*\*Réponse\*\*\s*:\s*(.+?)(?:\n\*\*|$)", raw, re.DOTALL)
    if m:
        answer = m.group(1).strip()

    # À faire (max 2)
    m2 = re.search(r"\*\*À faire\*\*\s*:\s*(.+?)(?:\n\*\*|$)", raw, re.DOTALL)
    if m2:
        block = m2.group(1).strip()
        recs = [
            line.lstrip("-•* ").strip()
            for line in block.split("\n")
            if line.strip()
        ][:2]

    # Alerte (optionnel)
    m3 = re.search(r"\*\*Alerte\*\*\s*:\s*(.+)", raw, re.IGNORECASE)
    if m3:
        alert = m3.group(1).strip() or None

    # Fallback si parsing échoue
    if not answer:
        answer = raw[:300].strip()

    return answer, recs, alert


# ── POST /coach/quick-advice (LOT 18) ────────────────────────────────────────

@coach_router.post(
    "/quick-advice",
    response_model=QuickAdviceResponse,
    status_code=status.HTTP_200_OK,
    summary="Conseil rapide SOMA (sans persistence)",
)
async def get_quick_advice(
    body: QuickAdviceRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.AI_COACH)),
):
    """
    Génère un conseil rapide en 3 phrases maximum.

    Différent de /coach/ask :
    - Pas de persistence en base (pas de thread, pas de message)
    - Contexte léger : readiness + twin + fatigue uniquement
    - Réponse structurée courte (Réponse + À faire + Alerte optionnelle)
    - Latence plus faible, idéal pour widget rapide mobile
    """
    from sqlalchemy import select as _select
    from app.models.user import UserProfile
    from app.services.context_builder import build_coach_context
    from app.services.claude_client import generate_coach_reply
    from app.core.analytics import track_event
    from app.core.config import settings

    # ── Profil utilisateur ────────────────────────────────────────────────
    prof_res = await db.execute(
        _select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = prof_res.scalar_one_or_none()

    # ── Contexte léger ────────────────────────────────────────────────────
    coach_ctx = await build_coach_context(db, current_user.id, profile)
    context_text = coach_ctx.to_prompt_text()

    # ── Résumé contexte compact ───────────────────────────────────────────
    context_parts: list[str] = []
    if coach_ctx.readiness_score is not None:
        context_parts.append(f"readiness: {coach_ctx.readiness_score:.0f}%")
    if coach_ctx.metabolic and coach_ctx.metabolic.fatigue_score is not None:
        context_parts.append(f"fatigue: {coach_ctx.metabolic.fatigue_score:.0f}%")
    if coach_ctx.twin_summary:
        status_part = coach_ctx.twin_summary.split(",")[0].replace("Statut ", "twin: ")
        context_parts.append(status_part)
    context_summary = ", ".join(context_parts) if context_parts else "données insuffisantes"

    # ── Confiance ─────────────────────────────────────────────────────────
    confidence = 0.5
    if coach_ctx.metabolic:
        confidence = max(0.4, coach_ctx.metabolic.confidence_score)
    elif coach_ctx.readiness_score is not None:
        confidence = 0.65

    # ── Appel Claude ──────────────────────────────────────────────────────
    try:
        raw_reply = await generate_coach_reply(
            question=body.question,
            context_text=context_text,
            conversation_history=None,
        )
    except Exception as exc:
        logger.error("quick-advice Claude error user %s : %s", current_user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la génération du conseil.",
        )

    answer, recs, alert = _parse_quick_reply(raw_reply)

    # ── Analytics (fire-and-forget) ───────────────────────────────────────
    await track_event(db, current_user.id, "quick_advice_requested", {
        "question_length": len(body.question),
    })

    model_used = "mock" if settings.CLAUDE_COACH_MOCK_MODE else settings.CLAUDE_COACH_MODEL

    return QuickAdviceResponse(
        answer=answer,
        recommendations=recs,
        alert=alert,
        confidence=round(confidence, 2),
        model_used=model_used,
        context_summary=context_summary,
    )


# ── POST /coach/ask ───────────────────────────────────────────────────────────

@coach_router.post("/ask", response_model=CoachAnswerResponse, status_code=status.HTTP_200_OK)
async def ask_coach_endpoint(
    body: AskCoachRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.AI_COACH)),
):
    """
    Pose une question au coach SOMA.

    Le coach analyse les données physiologiques du jour (nutrition, entraînement,
    sommeil, récupération, métriques) et génère une réponse personnalisée via Claude.

    - Si **thread_id** est fourni, la question s'inscrit dans le fil existant.
    - Si **thread_id** est absent, un nouveau fil est créé automatiquement.

    La réponse est structurée : synthèse, recommandations, alertes, confiance.
    """
    try:
        answer = await ask_coach(
            db=db,
            user_id=current_user.id,
            question=body.question,
            thread_id=body.thread_id,
        )
        await db.commit()
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.error("Erreur ask_coach user %s : %s", current_user.id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de la réponse : {exc}",
        )

    return CoachAnswerResponse(
        summary=answer.summary,
        full_response=answer.full_response,
        recommendations=answer.recommendations,
        warnings=answer.warnings,
        confidence=answer.confidence,
        context_tokens_estimate=answer.context_tokens_estimate,
        model_used=answer.model_used,
        thread_id=answer.thread_id,
        message_id=answer.message_id,
    )


# ── POST /coach/thread ────────────────────────────────────────────────────────

@coach_router.post(
    "/thread",
    response_model=ConversationThreadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation_thread(
    body: CreateThreadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.AI_COACH)),
):
    """
    Crée un nouveau fil de conversation vide.
    Utile pour regrouper des questions liées à un sujet précis.
    """
    thread = await create_thread(db, current_user.id, title=body.title)
    await db.commit()
    return thread


# ── GET /coach/history ────────────────────────────────────────────────────────

@coach_router.get("/history", response_model=ThreadListResponse)
async def list_conversation_threads(
    limit: int = Query(20, ge=1, le=100, description="Nombre de fils à retourner."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les fils de conversation de l'utilisateur (du plus récent au plus ancien).
    """
    threads = await get_threads(db, current_user.id, limit=limit)
    return ThreadListResponse(
        threads=[ConversationThreadResponse.model_validate(t) for t in threads],
        total=len(threads),
    )


# ── GET /coach/history/{thread_id} ───────────────────────────────────────────

@coach_router.get(
    "/history/{thread_id}",
    response_model=ConversationThreadDetailResponse,
)
async def get_thread_detail(
    thread_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200, description="Nb max de messages."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne le détail d'un fil de conversation avec tous ses messages.
    Vérifie que le fil appartient à l'utilisateur courant.
    """
    try:
        messages = await get_messages(db, thread_id, current_user.id, limit=limit)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    # Récupérer le thread pour le retourner aussi
    from sqlalchemy import select
    from app.models.coach import ConversationThread
    thread_res = await db.execute(
        select(ConversationThread).where(ConversationThread.id == thread_id)
    )
    thread = thread_res.scalar_one_or_none()

    return ConversationThreadDetailResponse(
        thread=ConversationThreadResponse.model_validate(thread),
        messages=[ConversationMessageResponse.model_validate(m) for m in messages],
    )

"""
Service ReadinessScore — persistance du score de récupération journalier (LOT 2).

Workflow :
  1. Le dashboard appelle compute_and_persist_readiness() après avoir collecté
     les données du jour.
  2. Le service calcule le score via compute_recovery_score_v1 (existant).
  3. Il upsert le résultat dans readiness_scores (unique sur user_id + score_date).
  4. Les endpoints /scores/readiness/* lisent directement depuis la table.

Stratégie upsert :
  - Vérifie l'existence par (user_id, score_date)
  - Si existant et données fraîches (< 1h) : ne recalcule pas sauf si recompute=True
  - Si existant et données anciennes ou recompute=True : mise à jour
  - Si absent : insert
"""
from datetime import date, datetime, timezone, timedelta
from typing import Optional, List
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.scores import ReadinessScore
from app.schemas.dashboard import SleepSummary, RecoverySummary
from app.schemas.scores import ReadinessScoreResponse, ReadinessScoreHistoryResponse
from app.services.dashboard_service import compute_recovery_score_v1

# Durée minimale entre deux recalculs automatiques (évite le recalcul sur chaque appel dashboard)
MIN_RECOMPUTE_INTERVAL_H = 1


async def compute_and_persist_readiness(
    db: AsyncSession,
    user_id: uuid.UUID,
    score_date: date,
    sleep: SleepSummary,
    hrv_ms: Optional[float],
    resting_hr: Optional[float],
    last_workout_load: Optional[float],
    force_recompute: bool = False,
) -> ReadinessScore:
    """
    Calcule le score de récupération et le persiste en DB.

    Si un score existe déjà pour cette date et qu'il a été calculé il y a moins
    de MIN_RECOMPUTE_INTERVAL_H heures, le résultat existant est retourné sauf si
    force_recompute=True.
    """
    # Vérification score existant
    existing = await get_readiness_score(db, user_id, score_date)

    if existing and not force_recompute:
        freshness = datetime.now(timezone.utc) - existing.created_at.replace(tzinfo=timezone.utc)
        if freshness < timedelta(hours=MIN_RECOMPUTE_INTERVAL_H):
            return existing  # Score frais — pas besoin de recalculer

    # Calcul du score via la fonction V1 existante
    recovery = compute_recovery_score_v1(sleep, hrv_ms, resting_hr, last_workout_load)

    # Méta sur les données utilisées
    variables_used = {
        "sleep_available": sleep.duration_minutes is not None,
        "hrv_available": hrv_ms is not None,
        "resting_hr_available": resting_hr is not None,
        "training_load_available": last_workout_load is not None,
        "sleep_minutes": sleep.duration_minutes,
        "hrv_ms": hrv_ms,
        "resting_hr_bpm": resting_hr,
        "last_workout_load": last_workout_load,
    }

    now = datetime.now(timezone.utc)

    if existing:
        # Mise à jour
        existing.overall_readiness = recovery.readiness_score
        existing.sleep_score = recovery.sleep_contribution
        existing.hrv_score = recovery.hrv_contribution
        existing.training_load_score = recovery.training_load_contribution
        existing.recovery_score = recovery.recovery_score
        existing.recommended_intensity = recovery.recommended_intensity
        existing.reasoning = recovery.reasoning
        existing.confidence_score = recovery.confidence
        existing.variables_used = variables_used
        existing.algorithm_version = "v1.0"
        existing.updated_at = now
        await db.flush()
        return existing

    # Insert
    readiness = ReadinessScore(
        user_id=user_id,
        score_date=score_date,
        overall_readiness=recovery.readiness_score,
        sleep_score=recovery.sleep_contribution,
        hrv_score=recovery.hrv_contribution,
        training_load_score=recovery.training_load_contribution,
        recovery_score=recovery.recovery_score,
        recommended_intensity=recovery.recommended_intensity,
        reasoning=recovery.reasoning,
        confidence_score=recovery.confidence,
        variables_used=variables_used,
        algorithm_version="v1.0",
        updated_at=now,
    )
    db.add(readiness)
    await db.flush()
    await db.refresh(readiness)
    return readiness


async def get_readiness_score(
    db: AsyncSession,
    user_id: uuid.UUID,
    score_date: date,
) -> Optional[ReadinessScore]:
    """Récupère le score de récupération d'une date donnée."""
    result = await db.execute(
        select(ReadinessScore).where(and_(
            ReadinessScore.user_id == user_id,
            ReadinessScore.score_date == score_date,
        ))
    )
    return result.scalar_one_or_none()


async def get_readiness_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    days: int = 30,
) -> ReadinessScoreHistoryResponse:
    """Retourne l'historique des scores sur N jours (ordre décroissant)."""
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=days - 1)

    result = await db.execute(
        select(ReadinessScore)
        .where(and_(
            ReadinessScore.user_id == user_id,
            ReadinessScore.score_date >= cutoff,
        ))
        .order_by(ReadinessScore.score_date.desc())
    )
    records = result.scalars().all()

    date_from = records[-1].score_date if records else None
    date_to = records[0].score_date if records else None

    return ReadinessScoreHistoryResponse(
        history=[ReadinessScoreResponse.model_validate(r) for r in records],
        days_requested=days,
        days_available=len(records),
        date_from=date_from,
        date_to=date_to,
    )

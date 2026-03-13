"""
Endpoints Predictive Health Engine — SOMA LOT 10.

Routes :
  GET /health/predictions     → 3 prédictions combinées (injury risk + overtraining + weight)
  GET /health/injury-risk     → Risque de blessure seul
  GET /health/overtraining    → Risque de surentraînement seul
"""
import logging
import uuid
from dataclasses import asdict
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.entitlements import require_feature
from app.core.features import FeatureCode
from app.db.session import get_db
from app.models.metrics import DailyMetrics
from app.models.scores import MetabolicStateSnapshot, ReadinessScore
from app.models.user import User
from app.models.vision_session import VisionSession
from app.schemas.predictions import (
    HealthPredictionsResponse,
    InjuryRiskResponse,
    OvertrainingResponse,
    WeightPredictionResponse,
)
from app.services.injury_risk_engine import compute_injury_risk
from app.services.overtraining_engine import compute_overtraining_risk
from app.services.weight_prediction_engine import compute_weight_predictions

logger = logging.getLogger(__name__)

predictions_router = APIRouter(prefix="/health", tags=["Predictions"])


# ── Helpers de chargement DB ───────────────────────────────────────────────────

async def _load_metabolic_snapshot(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> Optional[MetabolicStateSnapshot]:
    """Charge le snapshot métabolique du jour (ou du plus récent disponible)."""
    result = await db.execute(
        select(MetabolicStateSnapshot)
        .where(
            MetabolicStateSnapshot.user_id == user_id,
            MetabolicStateSnapshot.snapshot_date <= target_date,
        )
        .order_by(MetabolicStateSnapshot.snapshot_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _load_readiness(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> Optional[ReadinessScore]:
    """Charge le score de récupération du jour ou du plus récent."""
    result = await db.execute(
        select(ReadinessScore)
        .where(
            ReadinessScore.user_id == user_id,
            ReadinessScore.score_date <= target_date,
        )
        .order_by(ReadinessScore.score_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _load_daily_metrics_7d(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> list[DailyMetrics]:
    """Charge les DailyMetrics des 7 derniers jours pour calories avg + poids."""
    from_date = target_date - timedelta(days=7)
    result = await db.execute(
        select(DailyMetrics)
        .where(
            DailyMetrics.user_id == user_id,
            DailyMetrics.metrics_date >= from_date,
            DailyMetrics.metrics_date <= target_date,
        )
        .order_by(DailyMetrics.metrics_date.desc())
    )
    return list(result.scalars().all())


async def _load_vision_sessions_7d(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> list[VisionSession]:
    """Charge les VisionSessions des 7 derniers jours pour le proxy biomécanique."""
    from_date = target_date - timedelta(days=7)
    result = await db.execute(
        select(VisionSession)
        .where(
            VisionSession.user_id == user_id,
            VisionSession.session_date >= from_date,
            VisionSession.session_date <= target_date,
        )
    )
    return list(result.scalars().all())


def _avg_vision_quality(sessions: list[VisionSession]) -> Optional[float]:
    """
    Calcule la qualité biomécanique moyenne sur les VisionSessions récentes.
    Utilise la moyenne de (stability_score + amplitude_score) / 2 par session.
    Retourne None si aucune session ou aucun score disponible.
    """
    scores: list[float] = []
    for s in sessions:
        sub: list[float] = []
        if s.stability_score is not None:
            sub.append(s.stability_score)
        if s.amplitude_score is not None:
            sub.append(s.amplitude_score)
        if sub:
            scores.append(sum(sub) / len(sub))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 1)


def _avg_calories(metrics: list[DailyMetrics]) -> Optional[float]:
    """Moyenne des calories consommées sur la période (None si pas de données)."""
    vals = [m.calories_consumed for m in metrics if m.calories_consumed is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


def _latest_weight(metrics: list[DailyMetrics]) -> Optional[float]:
    """Poids le plus récent disponible dans les DailyMetrics."""
    for m in metrics:  # triés par date desc
        if m.weight_kg is not None:
            return m.weight_kg
    return None


# ── Assemblage des inputs par moteur ──────────────────────────────────────────

class _PredictionInputs:
    """Agrège tous les inputs nécessaires aux 3 moteurs en un seul chargement DB."""

    def __init__(
        self,
        metabolic: Optional[MetabolicStateSnapshot],
        readiness: Optional[ReadinessScore],
        metrics_7d: list[DailyMetrics],
        vision_7d: list[VisionSession],
    ):
        self.metabolic = metabolic
        self.readiness = readiness
        self.metrics_7d = metrics_7d
        self.vision_7d = vision_7d

        # Valeurs extraites
        self.training_load_7d = metabolic.training_load_7d if metabolic else None
        self.training_load_28d = metabolic.training_load_28d if metabolic else None
        self.fatigue_score = metabolic.fatigue_score if metabolic else None
        self.estimated_tdee_kcal = metabolic.estimated_tdee_kcal if metabolic else None

        self.readiness_score = readiness.overall_readiness if readiness else None
        self.sleep_score = readiness.sleep_score if readiness else None

        self.avg_vision_quality = _avg_vision_quality(vision_7d)
        self.calories_avg = _avg_calories(metrics_7d)
        self.current_weight_kg = _latest_weight(metrics_7d)
        self.active_calories_kcal = (
            _avg_calories_active(metrics_7d)
        )


def _avg_calories_active(metrics: list[DailyMetrics]) -> Optional[float]:
    """Moyenne des calories actives (fallback TDEE)."""
    vals = [m.active_calories_kcal for m in metrics if m.active_calories_kcal is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


async def _load_all_inputs(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: date,
) -> _PredictionInputs:
    """Charge en parallèle toutes les données nécessaires aux 3 moteurs."""
    metabolic, readiness, metrics_7d, vision_7d = (
        await _load_metabolic_snapshot(db, user_id, target_date),
        await _load_readiness(db, user_id, target_date),
        await _load_daily_metrics_7d(db, user_id, target_date),
        await _load_vision_sessions_7d(db, user_id, target_date),
    )
    return _PredictionInputs(metabolic, readiness, metrics_7d, vision_7d)


# ── Conversions dataclass → schéma Pydantic ───────────────────────────────────

def _injury_to_schema(result) -> InjuryRiskResponse:
    return InjuryRiskResponse(
        injury_risk_score=result.injury_risk_score,
        risk_level=result.risk_level,
        risk_area=result.risk_area,
        primary_risk_factor=result.primary_risk_factor,
        acwr=result.acwr,
        components=result.components,
        recommendations=result.recommendations,
        confidence=result.confidence,
    )


def _overtraining_to_schema(result) -> OvertrainingResponse:
    return OvertrainingResponse(
        overtraining_risk=result.overtraining_risk,
        risk_level=result.risk_level,
        acwr=result.acwr,
        acwr_zone=result.acwr_zone,
        recommendation=result.recommendation,
        components=result.components,
        confidence=result.confidence,
    )


def _weight_to_schema(result) -> WeightPredictionResponse:
    return WeightPredictionResponse(
        current_weight_kg=result.current_weight_kg,
        expected_weight_7d=result.expected_weight_7d,
        expected_weight_14d=result.expected_weight_14d,
        expected_weight_30d=result.expected_weight_30d,
        daily_energy_balance_kcal=result.daily_energy_balance_kcal,
        weekly_weight_change_kg=result.weekly_weight_change_kg,
        trend_direction=result.trend_direction,
        confidence=result.confidence,
        assumptions=result.assumptions,
    )


# ── GET /health/predictions ────────────────────────────────────────────────────

@predictions_router.get("/predictions", response_model=HealthPredictionsResponse)
async def get_health_predictions(
    target_date: Optional[date] = Query(None, description="Date de référence (YYYY-MM-DD). Défaut : aujourd'hui."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les 3 prédictions santé combinées pour l'utilisateur.

    - **injury_risk** : risque de blessure (ACWR + fatigue + biomécanique + récupération)
    - **overtraining** : risque de surentraînement (ACWR + bien-être + récupération)
    - **weight_prediction** : prédiction pondérale 7/14/30 jours (bilan énergétique)

    Tous les moteurs sont déterministes et indépendants du LLM.
    La `confidence` reflète la proportion de données disponibles (0 = pas de données, 1 = toutes).
    """
    date_ = target_date or date.today()
    logger.info("GET /health/predictions user=%s date=%s", current_user.id, date_)

    inputs = await _load_all_inputs(db, current_user.id, date_)

    injury = compute_injury_risk(
        training_load_7d=inputs.training_load_7d,
        training_load_28d=inputs.training_load_28d,
        fatigue_score=inputs.fatigue_score,
        avg_vision_quality=inputs.avg_vision_quality,
        readiness_score=inputs.readiness_score,
    )

    overtraining = compute_overtraining_risk(
        training_load_7d=inputs.training_load_7d,
        training_load_28d=inputs.training_load_28d,
        sleep_score=inputs.sleep_score,
        fatigue_score=inputs.fatigue_score,
        readiness_score=inputs.readiness_score,
    )

    weight = compute_weight_predictions(
        current_weight_kg=inputs.current_weight_kg,
        calories_consumed_avg=inputs.calories_avg,
        estimated_tdee_kcal=inputs.estimated_tdee_kcal,
        active_calories_kcal=inputs.active_calories_kcal,
    )

    return HealthPredictionsResponse(
        injury_risk=_injury_to_schema(injury),
        overtraining=_overtraining_to_schema(overtraining),
        weight_prediction=_weight_to_schema(weight),
        target_date=str(date_),
    )


# ── GET /health/injury-risk ────────────────────────────────────────────────────

@predictions_router.get("/injury-risk", response_model=InjuryRiskResponse)
async def get_injury_risk(
    target_date: Optional[date] = Query(None, description="Date de référence. Défaut : aujourd'hui."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.INJURY_PREDICTION)),
):
    """
    Calcule le risque de blessure actuel.

    Combine :
    - **ACWR** (poids 35%) : ratio charge aiguë/chronique — zone sûre 0.8–1.3
    - **Fatigue** (poids 25%) : score de fatigue musculaire et systémique
    - **Biomécanique** (poids 25%) : qualité de mouvement des sessions Computer Vision
    - **Récupération** (poids 15%) : score de readiness global

    Niveaux : `low` (<25) | `moderate` (25–49) | `high` (50–74) | `critical` (≥75)
    """
    date_ = target_date or date.today()
    logger.info("GET /health/injury-risk user=%s date=%s", current_user.id, date_)

    inputs = await _load_all_inputs(db, current_user.id, date_)

    result = compute_injury_risk(
        training_load_7d=inputs.training_load_7d,
        training_load_28d=inputs.training_load_28d,
        fatigue_score=inputs.fatigue_score,
        avg_vision_quality=inputs.avg_vision_quality,
        readiness_score=inputs.readiness_score,
    )

    return _injury_to_schema(result)


# ── GET /health/overtraining ───────────────────────────────────────────────────

@predictions_router.get("/overtraining", response_model=OvertrainingResponse)
async def get_overtraining_risk(
    target_date: Optional[date] = Query(None, description="Date de référence. Défaut : aujourd'hui."),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_feature(FeatureCode.TRAINING_LOAD)),
):
    """
    Évalue le risque de surentraînement.

    Combine :
    - **ACWR** (poids 40%) : principal indicateur — zone optimale 0.8–1.3
    - **Bien-être** (poids 35%) : sommeil + fatigue accumulée
    - **Récupération** (poids 25%) : score de readiness

    Zones ACWR : `undertraining` | `optimal` | `moderate_risk` | `high_risk` | `overreaching`
    """
    date_ = target_date or date.today()
    logger.info("GET /health/overtraining user=%s date=%s", current_user.id, date_)

    inputs = await _load_all_inputs(db, current_user.id, date_)

    result = compute_overtraining_risk(
        training_load_7d=inputs.training_load_7d,
        training_load_28d=inputs.training_load_28d,
        sleep_score=inputs.sleep_score,
        fatigue_score=inputs.fatigue_score,
        readiness_score=inputs.readiness_score,
    )

    return _overtraining_to_schema(result)

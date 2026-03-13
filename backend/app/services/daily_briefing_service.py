"""Daily Briefing Service — LOT 18.

Agrège les données de santé du jour en un briefing matinal unifié.

Principe : agrégateur pur (lecture DB uniquement, pas de calcul).
Sources :
  1. DailyMetrics        — cibles nutritionnelles, hydratation
  2. ReadinessScore      — récupération, intensité recommandée
  3. DigitalTwinSnapshot — statut global + préoccupation principale
  4. DailyRecommendation — plan entraînement + morning_briefing IA
  5. Insight             — top insight non lu

Le résultat est un dataclass sérialisable, prêt pour l'endpoint FastAPI.
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metrics import DailyMetrics
from app.models.scores import ReadinessScore, DailyRecommendation
from app.models.advanced import DigitalTwinSnapshot
from app.models.insights import Insight

logger = logging.getLogger(__name__)

# Seuils couleur readiness
_COLOR_GOOD = "#34C759"      # vert : ≥ 75
_COLOR_MODERATE = "#FF9500"  # orange : ≥ 50
_COLOR_LOW = "#FF3B30"       # rouge : < 50

# Longueur max du coach tip extrait du morning_briefing
_COACH_TIP_MAX_LEN = 250


@dataclass
class DailyBriefing:
    """Briefing journalier agrégé pour l'écran d'accueil quotidien."""

    briefing_date: date
    generated_at: datetime

    # ── Récupération ──────────────────────────────────────────────────────────
    readiness_score: Optional[float] = None        # 0-100
    readiness_level: Optional[str] = None          # "low"|"moderate"|"good"|"excellent"
    readiness_color: str = _COLOR_MODERATE         # hex code
    recommended_intensity: Optional[str] = None    # "rest"|"light"|"moderate"|"normal"|"push"

    # ── Sommeil ───────────────────────────────────────────────────────────────
    sleep_duration_h: Optional[float] = None
    sleep_quality_label: Optional[str] = None      # "poor"|"fair"|"good"|"excellent"

    # ── Entraînement ──────────────────────────────────────────────────────────
    training_type: Optional[str] = None            # ex: "Force", "Cardio", "Repos actif"
    training_intensity: Optional[str] = None       # ex: "Modéré", "Léger"
    training_duration_min: Optional[int] = None

    # ── Nutrition ─────────────────────────────────────────────────────────────
    calorie_target: Optional[float] = None
    protein_target_g: Optional[float] = None
    carb_target_g: Optional[float] = None
    fat_target_g: Optional[float] = None
    hydration_target_ml: int = 2500

    # ── Jumeau numérique ──────────────────────────────────────────────────────
    twin_status: Optional[str] = None              # "fresh"|"good"|"moderate"|"tired"|"critical"
    twin_primary_concern: Optional[str] = None

    # ── Alertes & insights ────────────────────────────────────────────────────
    alerts: list[str] = field(default_factory=list)  # max 3
    top_insight: Optional[str] = None              # message de l'insight non lu le plus récent
    coach_tip: Optional[str] = None                # extrait du morning_briefing IA


def _readiness_level(score: Optional[float]) -> str:
    """Convertit un score 0-100 en libellé de niveau."""
    if score is None:
        return "moderate"
    if score >= 80:
        return "excellent"
    if score >= 65:
        return "good"
    if score >= 45:
        return "moderate"
    return "low"


def _readiness_color(score: Optional[float]) -> str:
    """Retourne la couleur hex correspondant au score de récupération."""
    if score is None:
        return _COLOR_MODERATE
    if score >= 75:
        return _COLOR_GOOD
    if score >= 50:
        return _COLOR_MODERATE
    return _COLOR_LOW


def _extract_coach_tip(morning_briefing: Optional[str]) -> Optional[str]:
    """Extrait les N premiers caractères du morning briefing comme coach tip.

    Le morning_briefing est un texte Markdown. On prend la première phrase
    ou la première ligne non vide, tronquée à _COACH_TIP_MAX_LEN.
    """
    if not morning_briefing:
        return None
    # Retirer les astérisques markdown
    clean = morning_briefing.replace("**", "").replace("*", "").strip()
    # Prendre jusqu'au premier double saut de ligne ou point
    for sep in ["\n\n", ". "]:
        idx = clean.find(sep)
        if idx > 20:  # au moins 20 chars
            tip = clean[:idx + 1].strip()
            return tip[:_COACH_TIP_MAX_LEN]
    return clean[:_COACH_TIP_MAX_LEN]


async def compute_daily_briefing(
    db: AsyncSession,
    user_id: uuid.UUID,
    target_date: Optional[date] = None,
) -> DailyBriefing:
    """Agrège les données du jour en un DailyBriefing.

    Args:
        db: Session async SQLAlchemy.
        user_id: UUID de l'utilisateur.
        target_date: Date cible (défaut : aujourd'hui UTC).

    Returns:
        DailyBriefing avec les données disponibles. Les champs manquants
        gardent leur valeur par défaut (None ou valeur par défaut).
    """
    today = target_date or datetime.now(timezone.utc).date()

    briefing = DailyBriefing(
        briefing_date=today,
        generated_at=datetime.now(timezone.utc),
    )

    # ── 1. ReadinessScore ─────────────────────────────────────────────────────
    try:
        readiness_row = (await db.execute(
            select(ReadinessScore)
            .where(and_(
                ReadinessScore.user_id == user_id,
                ReadinessScore.score_date == today,
            ))
        )).scalar_one_or_none()

        if readiness_row:
            score = readiness_row.overall_readiness
            briefing.readiness_score = score
            briefing.readiness_level = _readiness_level(score)
            briefing.readiness_color = _readiness_color(score)
            briefing.recommended_intensity = readiness_row.recommended_intensity
    except Exception:
        logger.debug("briefing: could not load readiness", exc_info=True)

    # ── 2. DailyMetrics ───────────────────────────────────────────────────────
    try:
        metrics_row = (await db.execute(
            select(DailyMetrics)
            .where(and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.metrics_date == today,
            ))
        )).scalar_one_or_none()

        if metrics_row:
            briefing.calorie_target = metrics_row.calories_target
            briefing.protein_target_g = metrics_row.protein_target_g
            # carb_target et fat_target peuvent ne pas exister selon la version du schéma
            briefing.hydration_target_ml = metrics_row.hydration_target_ml or 2500

            # Sommeil (minutes → heures)
            if metrics_row.sleep_minutes is not None:
                briefing.sleep_duration_h = round(metrics_row.sleep_minutes / 60, 1)
            briefing.sleep_quality_label = metrics_row.sleep_quality_label
    except Exception:
        logger.debug("briefing: could not load daily_metrics", exc_info=True)

    # ── 3. DigitalTwinSnapshot ────────────────────────────────────────────────
    try:
        twin_row = (await db.execute(
            select(DigitalTwinSnapshot)
            .where(and_(
                DigitalTwinSnapshot.user_id == user_id,
                DigitalTwinSnapshot.snapshot_date == today,
            ))
        )).scalar_one_or_none()

        if twin_row:
            briefing.twin_status = twin_row.overall_status
            briefing.twin_primary_concern = twin_row.primary_concern

            # Ajouter les recommandations twin comme alertes (max 2 depuis twin)
            if twin_row.recommendations:
                recs = twin_row.recommendations
                if isinstance(recs, list):
                    briefing.alerts.extend(recs[:2])
    except Exception:
        logger.debug("briefing: could not load twin snapshot", exc_info=True)

    # ── 4. DailyRecommendation (plan + coach tip) ─────────────────────────────
    try:
        rec_row = (await db.execute(
            select(DailyRecommendation)
            .where(and_(
                DailyRecommendation.user_id == user_id,
                DailyRecommendation.recommendation_date == today,
            ))
        )).scalar_one_or_none()

        if rec_row:
            # Coach tip depuis le morning_briefing IA
            briefing.coach_tip = _extract_coach_tip(rec_row.morning_briefing)

            # Plan d'entraînement
            if rec_row.workout_recommendation and isinstance(rec_row.workout_recommendation, dict):
                wr = rec_row.workout_recommendation
                briefing.training_type = wr.get("type") or wr.get("workout_type")
                briefing.training_intensity = wr.get("intensity")
                dur = wr.get("duration_min") or wr.get("duration")
                if dur is not None:
                    try:
                        briefing.training_duration_min = int(dur)
                    except (ValueError, TypeError):
                        pass

            # Alertes depuis daily_plan
            if rec_row.daily_plan and isinstance(rec_row.daily_plan, dict):
                plan_alerts = rec_row.daily_plan.get("alerts", [])
                if isinstance(plan_alerts, list):
                    briefing.alerts.extend(plan_alerts[:2])

            # Hydratation target override
            if rec_row.hydration_target_ml:
                briefing.hydration_target_ml = rec_row.hydration_target_ml
    except Exception:
        logger.debug("briefing: could not load daily_recommendation", exc_info=True)

    # ── 5. Top Insight (non lu, non dismissé) ─────────────────────────────────
    try:
        insight_row = (await db.execute(
            select(Insight)
            .where(and_(
                Insight.user_id == user_id,
                Insight.is_read.is_(False),
                Insight.is_dismissed.is_(False),
            ))
            .order_by(desc(Insight.detected_at))
            .limit(1)
        )).scalar_one_or_none()

        if insight_row:
            briefing.top_insight = insight_row.message
    except Exception:
        logger.debug("briefing: could not load insight", exc_info=True)

    # ── Dédoublonnage et plafonnement des alertes ──────────────────────────────
    seen: set[str] = set()
    deduped: list[str] = []
    for alert in briefing.alerts:
        if alert and alert not in seen:
            seen.add(alert)
            deduped.append(alert)
    briefing.alerts = deduped[:3]  # max 3 alertes

    return briefing

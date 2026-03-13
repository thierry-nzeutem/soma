"""
Endpoint Home Summary SOMA — LOT 5.

GET /home/summary : agrégateur de démarrage de l'app mobile.

Réduit 5 appels API en 1 seul : métriques du jour, readiness, insights non lus,
plan santé (depuis le cache DailyRecommendation), et score longévité résumé.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import get_db
from app.models.user import User
from app.models.metrics import DailyMetrics
from app.models.scores import ReadinessScore, DailyRecommendation, LongevityScore
from app.models.insights import Insight
from app.core.deps import get_current_user
from app.schemas.home import (
    HomeSummaryResponse,
    HomeSummaryMetrics,
    HomeSummaryReadiness,
    HomeSummaryInsight,
    HomeSummaryPlan,
    HomeSummaryLongevity,
)
from app.services.daily_metrics_service import lazy_ensure_today_metrics


home_router = APIRouter(prefix="/home", tags=["Home"])


def _readiness_level(score: Optional[float]) -> str:
    if score is None:
        return "unknown"
    if score >= 80:
        return "excellent"
    if score >= 65:
        return "good"
    if score >= 45:
        return "fair"
    return "poor"


@home_router.get("/summary", response_model=HomeSummaryResponse)
async def get_home_summary(
    date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date cible (YYYY-MM-DD). Défaut : aujourd'hui.",
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Agrégateur de démarrage de l'app mobile.

    Remplace 5 appels API en un seul :
    - Métriques du jour (GET /metrics/daily)
    - Score de récupération (GET /scores/readiness/today)
    - Insights non lus (GET /insights?unread=true)
    - Plan santé du jour, depuis le cache DailyRecommendation (GET /health/plan/today)
    - Score longévité résumé (depuis dernière entrée DB)

    **Performance** : déclenche un lazy compute des métriques du jour si absent.
    Le plan santé est uniquement lu depuis le cache (pas de génération à la volée ici).
    """
    target_date = (
        datetime.strptime(date, "%Y-%m-%d").date()
        if date
        else datetime.now(timezone.utc).date()
    )
    now = datetime.now(timezone.utc)

    # Lazy compute des métriques si absentes (évite une réponse vide au premier appel)
    await lazy_ensure_today_metrics(db, current_user.id, target_date)

    # ── Métriques du jour ──────────────────────────────────────────────────────
    dm_res = await db.execute(
        select(DailyMetrics).where(and_(
            DailyMetrics.user_id == current_user.id,
            DailyMetrics.metrics_date == target_date,
        ))
    )
    dm = dm_res.scalar_one_or_none()
    metrics_summary: Optional[HomeSummaryMetrics] = None
    if dm:
        metrics_summary = HomeSummaryMetrics(
            metrics_date=dm.metrics_date,
            weight_kg=dm.weight_kg,
            calories_consumed=dm.calories_consumed,
            calories_target=dm.calories_target,
            protein_g=dm.protein_g,
            protein_target_g=dm.protein_target_g,
            hydration_ml=dm.hydration_ml,
            hydration_target_ml=dm.hydration_target_ml,
            steps=dm.steps,
            sleep_minutes=dm.sleep_minutes,
            sleep_quality_label=dm.sleep_quality_label,
            hrv_ms=dm.hrv_ms,
            workout_count=dm.workout_count or 0,
            readiness_score=dm.readiness_score,
            data_completeness_pct=dm.data_completeness_pct,
        )

    # ── Score de récupération ──────────────────────────────────────────────────
    rs_res = await db.execute(
        select(ReadinessScore).where(and_(
            ReadinessScore.user_id == current_user.id,
            ReadinessScore.score_date == target_date,
        ))
    )
    rs = rs_res.scalar_one_or_none()
    readiness_summary: Optional[HomeSummaryReadiness] = None
    if rs:
        readiness_summary = HomeSummaryReadiness(
            overall_readiness=rs.overall_readiness,
            recommended_intensity=rs.recommended_intensity,
            readiness_level=_readiness_level(rs.overall_readiness),
        )

    # ── Insights non lus (actifs, non dismissed) ──────────────────────────────
    ins_res = await db.execute(
        select(Insight).where(and_(
            Insight.user_id == current_user.id,
            Insight.is_read.is_(False),
            Insight.is_dismissed.is_(False),
        )).order_by(Insight.detected_at.desc()).limit(5)
    )
    insights = ins_res.scalars().all()
    insight_summaries = [
        HomeSummaryInsight(
            id=i.id,
            category=i.category,
            severity=i.severity,
            message=i.message,
        )
        for i in insights
    ]

    # Count total unread
    count_res = await db.execute(
        select(Insight).where(and_(
            Insight.user_id == current_user.id,
            Insight.is_read.is_(False),
            Insight.is_dismissed.is_(False),
        ))
    )
    total_unread = len(count_res.scalars().all())

    # ── Plan santé — depuis le cache DailyRecommendation uniquement ───────────
    plan_summary: Optional[HomeSummaryPlan] = None
    rec_res = await db.execute(
        select(DailyRecommendation).where(and_(
            DailyRecommendation.user_id == current_user.id,
            DailyRecommendation.recommendation_date == target_date,
        ))
    )
    rec = rec_res.scalar_one_or_none()
    if rec and rec.daily_plan:
        pd = rec.daily_plan
        plan_summary = HomeSummaryPlan(
            readiness_level=pd.get("readiness_level", "fair"),
            recommended_intensity=pd.get("recommended_intensity", "moderate"),
            protein_target_g=pd.get("protein_target_g", 0),
            calorie_target=pd.get("calorie_target", 0),
            steps_goal=pd.get("steps_goal", 8000),
            workout_recommendation=pd.get("workout_recommendation", {}),
            daily_tips=pd.get("daily_tips", []),
            alerts=pd.get("alerts", []),
            from_cache=True,
        )

    # ── Longévité — dernière entrée disponible (pas forcément aujourd'hui) ─────
    lon_res = await db.execute(
        select(LongevityScore).where(
            LongevityScore.user_id == current_user.id,
        ).order_by(LongevityScore.score_date.desc()).limit(1)
    )
    lon = lon_res.scalar_one_or_none()
    longevity_summary: Optional[HomeSummaryLongevity] = None
    if lon:
        longevity_summary = HomeSummaryLongevity(
            longevity_score=lon.longevity_score,
            biological_age_estimate=lon.biological_age_estimate,
        )

    return HomeSummaryResponse(
        summary_date=target_date,
        generated_at=now,
        metrics=metrics_summary,
        readiness=readiness_summary,
        unread_insights=insight_summaries,
        plan=plan_summary,
        longevity=longevity_summary,
        unread_insights_count=total_unread,
        has_active_plan=plan_summary is not None,
    )

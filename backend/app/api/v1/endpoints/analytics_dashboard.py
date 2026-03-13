"""Analytics Dashboard Endpoints — LOT 19.

Endpoints pour piloter le produit par les données.
Requièrent une authentification JWT standard.

Endpoints :
    GET /analytics/summary            — métriques DAU/WAU/MAU + engagement
    GET /analytics/events             — top événements par count
    GET /analytics/funnel/onboarding  — entonnoir onboarding 5 étapes
    GET /analytics/retention/cohorts  — cohortes hebdomadaires J1/J7/J30
    GET /analytics/features           — usage par fonctionnalité
    GET /analytics/coach              — métriques Coach IA
    GET /analytics/performance        — latences API (middleware buffer)

Note : En production, restreindre ces endpoints aux utilisateurs admin
       via une dépendance dédiée (is_admin sur le modèle User).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.analytics_dashboard import (
    AnalyticsSummaryResponse,
    EventCountResponse,
    OnboardingFunnelResponse,
    FunnelStepResponse,
    CohortRetentionResponse,
    FeatureUsageResponse,
    CoachAnalyticsResponse,
    ApiPerformanceStatsResponse,
)
from app.services.analytics_dashboard_service import (
    get_summary,
    get_events,
    get_funnel_onboarding,
    get_cohort_retention,
    get_feature_usage,
    get_coach_analytics,
    get_performance_stats,
)

analytics_dashboard_router = APIRouter(
    prefix="/analytics",
    tags=["Analytics Dashboard"],
)


# ── GET /analytics/summary ────────────────────────────────────────────────────

@analytics_dashboard_router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Résumé analytique global du produit",
)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="Période d'analyse en jours"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> AnalyticsSummaryResponse:
    """
    Retourne les métriques produit principales :
    - **DAU / WAU / MAU** et ratio de stickiness
    - Nombre total d'utilisateurs et nouveaux utilisateurs
    - Taux d'onboarding completion (%)
    - Entrées journal, questions coach, ouvertures briefing sur la période
    """
    s = await get_summary(db, days=days)
    return AnalyticsSummaryResponse(
        period_days=s.period_days,
        dau=s.dau,
        wau=s.wau,
        mau=s.mau,
        dau_mau_ratio=s.dau_mau_ratio,
        total_users=s.total_users,
        new_users=s.new_users,
        active_users=s.active_users,
        onboarding_completion_rate=s.onboarding_completion_rate,
        journal_entries=s.journal_entries,
        coach_questions=s.coach_questions,
        briefing_opens=s.briefing_opens,
    )


# ── GET /analytics/events ─────────────────────────────────────────────────────

@analytics_dashboard_router.get(
    "/events",
    response_model=list[EventCountResponse],
    summary="Top événements analytics par count",
)
async def get_analytics_events(
    days: int = Query(30, ge=1, le=365),
    event_name: Optional[str] = Query(None, description="Filtrer par nom d'événement"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[EventCountResponse]:
    """
    Retourne les événements analytics triés par nombre d'occurrences décroissant.
    Filtre optionnel par `event_name` pour zoomer sur un événement précis.
    """
    events = await get_events(db, days=days, event_name=event_name, limit=limit)
    return [
        EventCountResponse(
            event_name=e.event_name,
            count=e.count,
            unique_users=e.unique_users,
        )
        for e in events
    ]


# ── GET /analytics/funnel/onboarding ─────────────────────────────────────────

@analytics_dashboard_router.get(
    "/funnel/onboarding",
    response_model=OnboardingFunnelResponse,
    summary="Entonnoir d'onboarding 5 étapes",
)
async def get_onboarding_funnel(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> OnboardingFunnelResponse:
    """
    Calcule le funnel d'onboarding step-by-step :

    1. `app_open` → 2. `onboarding_complete` → 3. `morning_briefing_view`
    → 4. `journal_entry` → 5. `coach_question`

    Pour chaque étape : count d'utilisateurs, taux de conversion
    par rapport à l'étape précédente, et taux d'abandon (drop-off).
    """
    funnel = await get_funnel_onboarding(db, days=days)
    return OnboardingFunnelResponse(
        period_days=funnel.period_days,
        steps=[
            FunnelStepResponse(
                step_index=s.step_index,
                step_name=s.step_name,
                event_name=s.event_name,
                users_count=s.users_count,
                conversion_from_previous=s.conversion_from_previous,
                drop_off_rate=s.drop_off_rate,
            )
            for s in funnel.steps
        ],
        overall_conversion_rate=funnel.overall_conversion_rate,
    )


# ── GET /analytics/retention/cohorts ─────────────────────────────────────────

@analytics_dashboard_router.get(
    "/retention/cohorts",
    response_model=list[CohortRetentionResponse],
    summary="Cohortes de rétention hebdomadaires",
)
async def get_retention_cohorts(
    max_cohorts: int = Query(
        8, ge=1, le=52, description="Nombre max de cohortes hebdomadaires"
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CohortRetentionResponse]:
    """
    Retourne les cohortes d'utilisateurs groupées par semaine d'inscription
    (définie comme la semaine du premier événement analytics).

    Pour chaque cohorte :
    - `users_count` : taille de la cohorte
    - `retention_day1` : % actifs J+1 (fenêtre J+1 à J+2)
    - `retention_day7` : % actifs J+7 (fenêtre J+6 à J+8)
    - `retention_day30` : % actifs J+30 (fenêtre J+28 à J+32)

    Trié par semaine décroissante (plus récent en premier).
    """
    cohorts = await get_cohort_retention(db, max_cohorts=max_cohorts)
    return [
        CohortRetentionResponse(
            cohort_week=c.cohort_week,
            users_count=c.users_count,
            retention_day1=c.retention_day1,
            retention_day7=c.retention_day7,
            retention_day30=c.retention_day30,
        )
        for c in cohorts
    ]


# ── GET /analytics/features ───────────────────────────────────────────────────

@analytics_dashboard_router.get(
    "/features",
    response_model=FeatureUsageResponse,
    summary="Utilisation par fonctionnalité",
)
async def get_feature_usage_endpoint(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> FeatureUsageResponse:
    """
    Retourne le nombre d'utilisations de chaque fonctionnalité principale
    sur la période demandée :
    briefing, journal, coach, twin, nutrition, biomarqueurs, quick-advice, workout.
    """
    usage = await get_feature_usage(db, days=days)
    return FeatureUsageResponse(
        period_days=usage.period_days,
        briefing_views=usage.briefing_views,
        journal_entries=usage.journal_entries,
        coach_questions=usage.coach_questions,
        twin_views=usage.twin_views,
        nutrition_logs=usage.nutrition_logs,
        biomarker_logs=usage.biomarker_logs,
        quick_advice_requests=usage.quick_advice_requests,
        workout_logs=usage.workout_logs,
    )


# ── GET /analytics/coach ──────────────────────────────────────────────────────

@analytics_dashboard_router.get(
    "/coach",
    response_model=CoachAnalyticsResponse,
    summary="Métriques d'engagement du Coach IA",
)
async def get_coach_analytics_endpoint(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CoachAnalyticsResponse:
    """
    Retourne les métriques d'engagement du Coach IA :
    - questions totales + quick-advice
    - utilisateurs uniques ayant interagi avec le coach
    - questions par utilisateur actif
    - taux de follow-up (% ayant posé > 1 question — indicateur de satisfaction implicite)
    """
    coach = await get_coach_analytics(db, days=days)
    return CoachAnalyticsResponse(
        period_days=coach.period_days,
        total_questions=coach.total_questions,
        total_quick_advice=coach.total_quick_advice,
        unique_users_asking=coach.unique_users_asking,
        questions_per_active_user=coach.questions_per_active_user,
        follow_up_rate=coach.follow_up_rate,
    )


# ── GET /analytics/performance ────────────────────────────────────────────────

@analytics_dashboard_router.get(
    "/performance",
    response_model=list[ApiPerformanceStatsResponse],
    summary="Performances des endpoints API (buffer in-memory)",
)
async def get_api_performance(
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(get_current_user),
) -> list[ApiPerformanceStatsResponse]:
    """
    Retourne les statistiques de performance des endpoints API
    depuis le buffer in-memory du MetricsMiddleware.

    - `avg_response_ms` : temps moyen de réponse
    - `p95_response_ms` : percentile 95 (latence acceptable)
    - `total_calls` : nombre d'appels dans le buffer
    - `error_rate` : % d'appels retournant un status >= 400

    ⚠️ Le buffer est limité à 10 000 entrées (circulaire).
       En production, préférer un export vers Prometheus/Grafana.
    """
    stats = get_performance_stats(limit=limit)
    return [
        ApiPerformanceStatsResponse(
            endpoint=s.endpoint,
            method=s.method,
            avg_response_ms=s.avg_response_ms,
            p95_response_ms=s.p95_response_ms,
            total_calls=s.total_calls,
            error_rate=s.error_rate,
        )
        for s in stats
    ]

"""Analytics Dashboard Service — LOT 19.

Agrège les métriques produit depuis analytics_events pour le dashboard interne.
Toutes les fonctions sont async et opèrent directement sur AsyncSession.

Fonctions publiques :
    get_summary()           — DAU / WAU / MAU / ratio / onboarding / engagement
    get_events()            — top événements triés par count
    get_funnel_onboarding() — entonnoir onboarding 5 étapes step-by-step
    get_cohort_retention()  — cohortes hebdomadaires + rétention J1/J7/J30
    get_feature_usage()     — usage par fonctionnalité (briefing, journal, coach…)
    get_coach_analytics()   — métriques coach IA (questions, follow-up, quick-advice)
    get_performance_stats() — latences API depuis le buffer MetricsMiddleware

Design :
  - Fonctions pures sans état global.
  - Aucune dépendance en dehors de SQLAlchemy + stdlib.
  - Graceful sur valeurs nulles (toujours 0 ou 0.0, jamais None).
  - Tests unitaires sans DB via AsyncMock.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analytics import AnalyticsEventDB
from app.models.user import User

# ═══════════════════════════════════════════════════════════════════════════════
# Constantes
# ═══════════════════════════════════════════════════════════════════════════════

# Date de début des analytics (filtre pour requêtes "all-time")
_EPOCH = datetime(2024, 1, 1, tzinfo=timezone.utc)

# Étapes du funnel onboarding (ordre chronologique)
_FUNNEL_STEPS: list[tuple[str, str]] = [
    ("App Ouvert", "app_open"),
    ("Onboarding Complété", "onboarding_complete"),
    ("Premier Briefing", "morning_briefing_view"),
    ("Premier Journal", "journal_entry"),
    ("Première Question Coach", "coach_question"),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Dataclasses de résultat
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AnalyticsSummary:
    """Résumé analytique principal du produit."""
    period_days: int
    dau: int                          # Daily Active Users (aujourd'hui)
    wau: int                          # Weekly Active Users (7 derniers jours)
    mau: int                          # Monthly Active Users (30 derniers jours)
    dau_mau_ratio: float              # Indicateur de stickiness (0-1)
    total_users: int                  # Total utilisateurs en DB
    new_users: int                    # Nouveaux utilisateurs dans la période
    active_users: int                 # = mau
    onboarding_completion_rate: float  # % utilisateurs ayant terminé l'onboarding
    journal_entries: int              # Entrées journal dans la période
    coach_questions: int              # Questions coach dans la période
    briefing_opens: int               # Ouvertures briefing dans la période


@dataclass
class EventCount:
    """Count d'un événement analytics."""
    event_name: str
    count: int
    unique_users: int


@dataclass
class FunnelStep:
    """Étape d'un entonnoir de conversion."""
    step_index: int
    step_name: str
    event_name: str
    users_count: int
    conversion_from_previous: float   # % par rapport à l'étape précédente
    drop_off_rate: float              # % perdus à cette étape


@dataclass
class OnboardingFunnel:
    """Entonnoir onboarding complet."""
    period_days: int
    steps: list[FunnelStep]
    overall_conversion_rate: float    # taux de conversion global step 0 → step N


@dataclass
class CohortRetention:
    """Rétention d'une cohorte hebdomadaire."""
    cohort_week: str          # format "2026-W10"
    users_count: int
    retention_day1: float     # % utilisateurs actifs J+1
    retention_day7: float     # % utilisateurs actifs J+7
    retention_day30: float    # % utilisateurs actifs J+30


@dataclass
class FeatureUsage:
    """Utilisation de chaque fonctionnalité principale."""
    period_days: int
    briefing_views: int
    journal_entries: int
    coach_questions: int
    twin_views: int
    nutrition_logs: int
    biomarker_logs: int
    quick_advice_requests: int
    workout_logs: int


@dataclass
class CoachAnalytics:
    """Métriques d'engagement du Coach IA."""
    period_days: int
    total_questions: int
    total_quick_advice: int
    unique_users_asking: int
    questions_per_active_user: float
    follow_up_rate: float             # % users ayant posé > 1 question


@dataclass
class ApiPerformanceStats:
    """Statistiques de performance d'un endpoint."""
    endpoint: str
    method: str
    avg_response_ms: float
    p95_response_ms: float
    total_calls: int
    error_rate: float                 # % appels avec status >= 400


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers internes
# ═══════════════════════════════════════════════════════════════════════════════

def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _count_distinct_users(
    db: AsyncSession,
    since: datetime,
    event_name: Optional[str] = None,
) -> int:
    """Compte les utilisateurs distincts actifs depuis 'since'."""
    q = select(func.count(distinct(AnalyticsEventDB.user_id))).where(
        AnalyticsEventDB.created_at >= since
    )
    if event_name is not None:
        q = q.where(AnalyticsEventDB.event_name == event_name)
    r = await db.execute(q)
    return r.scalar_one() or 0


async def _count_events(
    db: AsyncSession,
    event_name: str,
    since: datetime,
) -> int:
    """Compte le nombre total d'occurrences d'un événement depuis 'since'."""
    r = await db.execute(
        select(func.count()).where(
            and_(
                AnalyticsEventDB.event_name == event_name,
                AnalyticsEventDB.created_at >= since,
            )
        )
    )
    return r.scalar_one() or 0


def _has_event_in_window(
    events: list[datetime],
    first_seen: datetime,
    day_start: int,
    day_end: int,
) -> bool:
    """Vérifie si l'utilisateur a un événement dans [first_seen+day_start, first_seen+day_end)."""
    window_start = first_seen + timedelta(days=day_start)
    window_end = first_seen + timedelta(days=day_end)
    return any(window_start <= dt < window_end for dt in events)


# ═══════════════════════════════════════════════════════════════════════════════
# Fonctions publiques
# ═══════════════════════════════════════════════════════════════════════════════

async def get_summary(db: AsyncSession, days: int = 30) -> AnalyticsSummary:
    """Agrège les métriques principales du produit sur la période donnée."""
    now = _now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    period_start = now - timedelta(days=days)

    # ── Métriques actifs ──────────────────────────────────────────────────────
    dau = await _count_distinct_users(db, today_start)
    wau = await _count_distinct_users(db, week_ago)
    mau = await _count_distinct_users(db, month_ago)
    dau_mau_ratio = round(dau / mau, 3) if mau > 0 else 0.0

    # ── Total utilisateurs ────────────────────────────────────────────────────
    total_r = await db.execute(select(func.count(User.id)))
    total_users = total_r.scalar_one() or 0

    # ── Nouveaux utilisateurs (premier événement dans la période) ─────────────
    first_event_subq = (
        select(
            AnalyticsEventDB.user_id,
            func.min(AnalyticsEventDB.created_at).label("first_seen"),
        )
        .group_by(AnalyticsEventDB.user_id)
        .subquery()
    )
    new_r = await db.execute(
        select(func.count())
        .select_from(first_event_subq)
        .where(first_event_subq.c.first_seen >= period_start)
    )
    new_users = new_r.scalar_one() or 0

    # ── Onboarding completion rate ────────────────────────────────────────────
    onboarding_users = await _count_distinct_users(db, _EPOCH, "onboarding_complete")
    onboarding_rate = (
        round(onboarding_users / total_users * 100, 1) if total_users > 0 else 0.0
    )

    # ── Événements d'engagement dans la période ───────────────────────────────
    journal_entries = await _count_events(db, "journal_entry", period_start)
    coach_questions = await _count_events(db, "coach_question", period_start)
    briefing_opens = await _count_events(db, "morning_briefing_view", period_start)

    return AnalyticsSummary(
        period_days=days,
        dau=dau,
        wau=wau,
        mau=mau,
        dau_mau_ratio=dau_mau_ratio,
        total_users=total_users,
        new_users=new_users,
        active_users=mau,
        onboarding_completion_rate=onboarding_rate,
        journal_entries=journal_entries,
        coach_questions=coach_questions,
        briefing_opens=briefing_opens,
    )


async def get_events(
    db: AsyncSession,
    days: int = 30,
    event_name: Optional[str] = None,
    limit: int = 20,
) -> list[EventCount]:
    """Retourne le top des événements par count sur la période."""
    period_start = _now() - timedelta(days=days)

    q = (
        select(
            AnalyticsEventDB.event_name,
            func.count().label("cnt"),
            func.count(distinct(AnalyticsEventDB.user_id)).label("unique_users"),
        )
        .where(AnalyticsEventDB.created_at >= period_start)
        .group_by(AnalyticsEventDB.event_name)
        .order_by(func.count().desc())
        .limit(limit)
    )
    if event_name is not None:
        q = q.where(AnalyticsEventDB.event_name == event_name)

    result = await db.execute(q)
    rows = result.fetchall()

    return [
        EventCount(
            event_name=row.event_name,
            count=row.cnt,
            unique_users=row.unique_users,
        )
        for row in rows
    ]


async def get_funnel_onboarding(
    db: AsyncSession,
    days: int = 30,
) -> OnboardingFunnel:
    """Calcule l'entonnoir onboarding en 5 étapes, step-by-step."""
    period_start = _now() - timedelta(days=days)

    # Count distinct users pour chaque étape
    step_counts: list[tuple[str, str, int]] = []
    for step_name, event in _FUNNEL_STEPS:
        count = await _count_distinct_users(db, period_start, event)
        step_counts.append((step_name, event, count))

    # Calcule conversion et drop-off pour chaque étape
    steps: list[FunnelStep] = []
    for i, (name, event, count) in enumerate(step_counts):
        if i == 0:
            conversion = 100.0
            drop_off = 0.0
        else:
            prev_count = step_counts[i - 1][2]
            conversion = round(count / prev_count * 100, 1) if prev_count > 0 else 0.0
            drop_off = round(100.0 - conversion, 1)

        steps.append(
            FunnelStep(
                step_index=i + 1,
                step_name=name,
                event_name=event,
                users_count=count,
                conversion_from_previous=conversion,
                drop_off_rate=drop_off,
            )
        )

    top_count = step_counts[0][2] if step_counts else 0
    last_count = step_counts[-1][2] if step_counts else 0
    overall = round(last_count / top_count * 100, 1) if top_count > 0 else 0.0

    return OnboardingFunnel(
        period_days=days,
        steps=steps,
        overall_conversion_rate=overall,
    )


async def get_cohort_retention(
    db: AsyncSession,
    max_cohorts: int = 8,
) -> list[CohortRetention]:
    """Calcule la rétention par cohorte hebdomadaire (max max_cohorts semaines)."""

    # Récupère le premier événement de chaque utilisateur
    first_event_subq = (
        select(
            AnalyticsEventDB.user_id,
            func.min(AnalyticsEventDB.created_at).label("first_seen"),
        )
        .group_by(AnalyticsEventDB.user_id)
        .subquery()
    )
    first_r = await db.execute(
        select(first_event_subq.c.user_id, first_event_subq.c.first_seen)
    )
    user_first_events = first_r.fetchall()

    if not user_first_events:
        return []

    # Groupe par semaine ISO (format "YYYY-WNN")
    cohorts: dict[str, list[tuple[uuid.UUID, datetime]]] = defaultdict(list)
    for user_id, first_seen in user_first_events:
        if first_seen.tzinfo is None:
            first_seen = first_seen.replace(tzinfo=timezone.utc)
        week_key = first_seen.strftime("%Y-W%W")
        cohorts[week_key].append((user_id, first_seen))

    results: list[CohortRetention] = []

    for week_key in sorted(cohorts.keys(), reverse=True)[:max_cohorts]:
        cohort_users = cohorts[week_key]
        cohort_size = len(cohort_users)
        user_ids = [uid for uid, _ in cohort_users]

        # Récupère tous les événements de la cohorte en 1 seule requête
        events_r = await db.execute(
            select(
                AnalyticsEventDB.user_id,
                AnalyticsEventDB.created_at,
            ).where(AnalyticsEventDB.user_id.in_(user_ids))
        )
        all_events = events_r.fetchall()

        # Index user_id → liste de datetimes
        user_events: dict[uuid.UUID, list[datetime]] = defaultdict(list)
        for uid, created_at in all_events:
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            user_events[uid].append(created_at)

        # Calcul rétention en Python (O(n) par cohorte)
        d1_count = d7_count = d30_count = 0
        for uid, first_seen in cohort_users:
            events = user_events.get(uid, [])
            if _has_event_in_window(events, first_seen, 1, 2):
                d1_count += 1
            if _has_event_in_window(events, first_seen, 6, 8):
                d7_count += 1
            if _has_event_in_window(events, first_seen, 28, 32):
                d30_count += 1

        results.append(
            CohortRetention(
                cohort_week=week_key,
                users_count=cohort_size,
                retention_day1=round(d1_count / cohort_size * 100, 1) if cohort_size > 0 else 0.0,
                retention_day7=round(d7_count / cohort_size * 100, 1) if cohort_size > 0 else 0.0,
                retention_day30=round(d30_count / cohort_size * 100, 1) if cohort_size > 0 else 0.0,
            )
        )

    return results


async def get_feature_usage(
    db: AsyncSession,
    days: int = 30,
) -> FeatureUsage:
    """Agrège le nombre d'utilisations de chaque fonctionnalité principale."""
    period_start = _now() - timedelta(days=days)

    briefing_views = await _count_events(db, "morning_briefing_view", period_start)
    journal_entries = await _count_events(db, "journal_entry", period_start)
    coach_questions = await _count_events(db, "coach_question", period_start)
    twin_views = await _count_events(db, "twin_viewed", period_start)
    nutrition_logs = await _count_events(db, "nutrition_logged", period_start)
    biomarker_logs = await _count_events(db, "biomarker_viewed", period_start)
    quick_advice = await _count_events(db, "quick_advice_requested", period_start)
    workout_logs = await _count_events(db, "workout_logged", period_start)

    return FeatureUsage(
        period_days=days,
        briefing_views=briefing_views,
        journal_entries=journal_entries,
        coach_questions=coach_questions,
        twin_views=twin_views,
        nutrition_logs=nutrition_logs,
        biomarker_logs=biomarker_logs,
        quick_advice_requests=quick_advice,
        workout_logs=workout_logs,
    )


async def get_coach_analytics(
    db: AsyncSession,
    days: int = 30,
) -> CoachAnalytics:
    """Métriques d'usage et d'engagement du Coach IA."""
    period_start = _now() - timedelta(days=days)

    total_questions = await _count_events(db, "coach_question", period_start)
    total_quick_advice = await _count_events(db, "quick_advice_requested", period_start)
    unique_users = await _count_distinct_users(db, period_start, "coach_question")
    questions_per_user = round(total_questions / unique_users, 2) if unique_users > 0 else 0.0

    # Follow-up rate : % users ayant posé plus d'une question
    multi_r = await db.execute(
        select(func.count()).select_from(
            select(
                AnalyticsEventDB.user_id,
                func.count().label("cnt"),
            )
            .where(
                and_(
                    AnalyticsEventDB.event_name == "coach_question",
                    AnalyticsEventDB.created_at >= period_start,
                )
            )
            .group_by(AnalyticsEventDB.user_id)
            .having(func.count() > 1)
            .subquery()
        )
    )
    multi_question_users = multi_r.scalar_one() or 0
    follow_up_rate = (
        round(multi_question_users / unique_users * 100, 1) if unique_users > 0 else 0.0
    )

    return CoachAnalytics(
        period_days=days,
        total_questions=total_questions,
        total_quick_advice=total_quick_advice,
        unique_users_asking=unique_users,
        questions_per_active_user=questions_per_user,
        follow_up_rate=follow_up_rate,
    )


def get_performance_stats(limit: int = 20) -> list[ApiPerformanceStats]:
    """Retourne les statistiques de performance API depuis le buffer middleware.

    Agrège par (endpoint, method), trie par volume d'appels décroissant.
    Retourne [] si le buffer est vide ou si le middleware n'est pas chargé.
    """
    try:
        from app.middleware.metrics_middleware import get_buffered_metrics
        records = get_buffered_metrics()
    except ImportError:
        return []

    if not records:
        return []

    # Agrège par (endpoint, method)
    endpoint_data: dict[tuple[str, str], list] = defaultdict(list)
    for record in records:
        key = (record.endpoint, record.method)
        endpoint_data[key].append(record)

    stats: list[ApiPerformanceStats] = []
    for (endpoint, method), ep_records in sorted(
        endpoint_data.items(),
        key=lambda x: len(x[1]),
        reverse=True,
    )[:limit]:
        times = sorted(r.response_time_ms for r in ep_records)
        avg_ms = sum(times) / len(times)
        p95_idx = max(0, int(len(times) * 0.95) - 1)
        p95_ms = times[p95_idx]
        errors = sum(1 for r in ep_records if r.status_code >= 400)

        stats.append(
            ApiPerformanceStats(
                endpoint=endpoint,
                method=method,
                avg_response_ms=round(avg_ms, 1),
                p95_response_ms=float(p95_ms),
                total_calls=len(times),
                error_rate=round(errors / len(times) * 100, 1),
            )
        )

    return stats

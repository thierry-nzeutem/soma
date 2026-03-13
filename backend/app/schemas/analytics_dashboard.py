"""Schémas Pydantic — Analytics Dashboard — LOT 19.

Schémas de réponse pour les endpoints GET /analytics/*.
Tous les champs numériques sont non-nullable (0 par défaut, jamais None).
"""
from __future__ import annotations

from pydantic import BaseModel, Field


# ── Résumé global ─────────────────────────────────────────────────────────────

class AnalyticsSummaryResponse(BaseModel):
    """Métriques produit principales."""

    period_days: int = Field(description="Période couverte en jours")
    dau: int = Field(description="Daily Active Users (aujourd'hui)")
    wau: int = Field(description="Weekly Active Users (7 derniers jours)")
    mau: int = Field(description="Monthly Active Users (30 derniers jours)")
    dau_mau_ratio: float = Field(description="Ratio DAU/MAU — indicateur de stickiness")
    total_users: int = Field(description="Total d'utilisateurs enregistrés")
    new_users: int = Field(description="Nouveaux utilisateurs dans la période")
    active_users: int = Field(description="Utilisateurs actifs dans la période (= MAU)")
    onboarding_completion_rate: float = Field(
        description="Taux d'onboarding complété en % (0-100)"
    )
    journal_entries: int = Field(description="Entrées journal dans la période")
    coach_questions: int = Field(description="Questions coach dans la période")
    briefing_opens: int = Field(description="Ouvertures briefing dans la période")

    model_config = {"from_attributes": True}


# ── Événements ────────────────────────────────────────────────────────────────

class EventCountResponse(BaseModel):
    """Count d'un événement analytics."""
    event_name: str
    count: int
    unique_users: int

    model_config = {"from_attributes": True}


# ── Funnel ────────────────────────────────────────────────────────────────────

class FunnelStepResponse(BaseModel):
    """Étape d'un entonnoir de conversion."""
    step_index: int
    step_name: str
    event_name: str
    users_count: int
    conversion_from_previous: float = Field(
        description="Taux de conversion par rapport à l'étape précédente (%)"
    )
    drop_off_rate: float = Field(description="Taux d'abandon à cette étape (%)")

    model_config = {"from_attributes": True}


class OnboardingFunnelResponse(BaseModel):
    """Entonnoir onboarding complet."""
    period_days: int
    steps: list[FunnelStepResponse]
    overall_conversion_rate: float = Field(
        description="Taux de conversion global step 0 → step N (%)"
    )

    model_config = {"from_attributes": True}


# ── Cohortes ──────────────────────────────────────────────────────────────────

class CohortRetentionResponse(BaseModel):
    """Rétention d'une cohorte hebdomadaire."""
    cohort_week: str = Field(description="Semaine de cohorte (format YYYY-WNN)")
    users_count: int = Field(description="Nombre d'utilisateurs dans la cohorte")
    retention_day1: float = Field(description="Rétention J+1 (%)")
    retention_day7: float = Field(description="Rétention J+7 (%)")
    retention_day30: float = Field(description="Rétention J+30 (%)")

    model_config = {"from_attributes": True}


# ── Feature usage ─────────────────────────────────────────────────────────────

class FeatureUsageResponse(BaseModel):
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

    model_config = {"from_attributes": True}


# ── Coach ─────────────────────────────────────────────────────────────────────

class CoachAnalyticsResponse(BaseModel):
    """Métriques d'engagement du Coach IA."""
    period_days: int
    total_questions: int
    total_quick_advice: int
    unique_users_asking: int
    questions_per_active_user: float
    follow_up_rate: float = Field(
        description="% utilisateurs ayant posé plus d'une question"
    )

    model_config = {"from_attributes": True}


# ── Performance API ───────────────────────────────────────────────────────────

class ApiPerformanceStatsResponse(BaseModel):
    """Statistiques de performance d'un endpoint."""
    endpoint: str
    method: str
    avg_response_ms: float
    p95_response_ms: float
    total_calls: int
    error_rate: float = Field(description="% appels avec status >= 400")

    model_config = {"from_attributes": True}

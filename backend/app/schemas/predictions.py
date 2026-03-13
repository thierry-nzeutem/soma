"""
Schémas Pydantic v2 — Predictive Health Engine SOMA (LOT 10).

Valident et sérialisent les réponses des endpoints de prédiction.
"""
from typing import Optional
from pydantic import BaseModel, Field


# ── InjuryRisk ────────────────────────────────────────────────────────────────

class InjuryRiskResponse(BaseModel):
    """Résultat du calcul du risque de blessure."""
    injury_risk_score: float = Field(
        ..., ge=0.0, le=100.0,
        description="Score de risque de blessure (0–100).",
    )
    risk_level: str = Field(
        ...,
        description="Niveau de risque : low / moderate / high / critical.",
    )
    risk_area: str = Field(
        ...,
        description="Zone primaire de risque : training_load / fatigue / biomechanics / recovery / combined / unknown.",
    )
    primary_risk_factor: str = Field(
        ...,
        description="Facteur de risque dominant.",
    )
    acwr: Optional[float] = Field(
        None,
        description="Ratio charge aiguë / chronique calculé (Acute:Chronic Workload Ratio).",
    )
    components: dict = Field(
        default_factory=dict,
        description="Scores bruts par composante (0–100).",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Recommandations contextualisées.",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confiance du score (0–1) proportionnelle aux données disponibles.",
    )


# ── Overtraining ──────────────────────────────────────────────────────────────

class OvertrainingResponse(BaseModel):
    """Résultat du calcul du risque de surentraînement."""
    overtraining_risk: float = Field(
        ..., ge=0.0, le=100.0,
        description="Score de risque de surentraînement (0–100).",
    )
    risk_level: str = Field(
        ...,
        description="Niveau de risque : low / moderate / high / critical.",
    )
    acwr: Optional[float] = Field(
        None,
        description="Ratio charge aiguë / chronique (ACWR).",
    )
    acwr_zone: str = Field(
        ...,
        description="Zone ACWR : undertraining / optimal / moderate_risk / high_risk / overreaching / unknown.",
    )
    recommendation: str = Field(
        ...,
        description="Recommandation principale (1 phrase).",
    )
    components: dict = Field(
        default_factory=dict,
        description="Scores bruts par composante (acwr, wellbeing, readiness).",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confiance du score (0–1).",
    )


# ── WeightPrediction ──────────────────────────────────────────────────────────

class WeightPredictionResponse(BaseModel):
    """Prédictions d'évolution du poids corporel."""
    current_weight_kg: Optional[float] = Field(
        None,
        description="Poids actuel (kg).",
    )
    expected_weight_7d: Optional[float] = Field(
        None,
        description="Poids prédit à 7 jours (kg).",
    )
    expected_weight_14d: Optional[float] = Field(
        None,
        description="Poids prédit à 14 jours (kg).",
    )
    expected_weight_30d: Optional[float] = Field(
        None,
        description="Poids prédit à 30 jours (kg).",
    )
    daily_energy_balance_kcal: Optional[float] = Field(
        None,
        description="Bilan énergétique journalier moyen (kcal). Positif = surplus, négatif = déficit.",
    )
    weekly_weight_change_kg: Optional[float] = Field(
        None,
        description="Delta de poids prévu sur 7 jours (kg).",
    )
    trend_direction: str = Field(
        ...,
        description="Tendance pondérale : loss / gain / stable.",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confiance des prédictions (0–1).",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Hypothèses du modèle pour transparence.",
    )


# ── Réponse combinée ──────────────────────────────────────────────────────────

class HealthPredictionsResponse(BaseModel):
    """Réponse agrégée des 3 moteurs prédictifs."""
    injury_risk: InjuryRiskResponse = Field(
        ..., description="Risque de blessure.",
    )
    overtraining: OvertrainingResponse = Field(
        ..., description="Risque de surentraînement.",
    )
    weight_prediction: WeightPredictionResponse = Field(
        ..., description="Prédiction d'évolution du poids.",
    )
    target_date: str = Field(
        ...,
        description="Date de référence des calculs (YYYY-MM-DD).",
    )

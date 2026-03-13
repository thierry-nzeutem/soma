"""
Biological Age Engine — LOT 11.

Builds on longevity_engine.py component scores + MetabolicTwin metabolic_age +
ReadinessScore to produce a structured, multi-component biological age estimate.

7 components:
  cardiovascular   20%  (cardio_score from longevity_engine)
  metabolic        20%  (metabolic_age from MetabolicTwin → converted to score)
  body_composition 15%  (weight_score + optional body_comp_score)
  sleep            15%  (sleep_score from longevity_engine)
  activity         15%  (strength_score from longevity_engine)
  recovery         10%  (readiness_score from ReadinessScore — NEW LOT 11)
  consistency       5%  (consistency_score from longevity_engine)

Formula (same reference as longevity_engine):
  score_to_delta(s) = (75 - s) × 0.2   →  ref score 75 = 0 years delta
  component_age_delta = weight × (75 - score) × 0.2
  biological_age = chronological_age + Σ(component_age_delta)
  biological_age ∈ [chrono - 15, chrono + 15]

All compute functions are pure and have no DB access.
"""
from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

LONGEVITY_REFERENCE_SCORE = 75.0          # score neutral → bio_age = chrono_age
YEARS_PER_SCORE_POINT = 0.2               # 1 point score = 0.2 years younger/older
BIO_AGE_CLAMP_YEARS = 15.0               # max deviation from chronological age

# Component weights — must sum to 1.0
COMPONENT_WEIGHTS: dict[str, float] = {
    "cardiovascular":   0.20,
    "metabolic":        0.20,
    "body_composition": 0.15,
    "sleep":            0.15,
    "activity":         0.15,
    "recovery":         0.10,
    "consistency":      0.05,
}

# Threshold below which a lever is triggered
LEVER_TRIGGER_THRESHOLD = 65.0


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class BiologicalAgeComponent:
    """A single biological age factor with its score and age contribution."""
    factor_name: str                # e.g. "cardiovascular"
    display_name: str               # e.g. "Santé cardiovasculaire"
    score: float                    # 0-100 (100 = excellent longevity)
    weight: float                   # relative importance (0-1)
    age_delta_years: float          # contribution in years (negative = younger)
    explanation: str                # human-readable explanation of the score
    is_available: bool = True       # False if input data was missing

    def to_dict(self) -> dict:
        return {
            "factor_name": self.factor_name,
            "display_name": self.display_name,
            "score": self.score,
            "weight": self.weight,
            "age_delta_years": self.age_delta_years,
            "explanation": self.explanation,
            "is_available": self.is_available,
        }


@dataclass
class BiologicalAgeLever:
    """An actionable intervention to reduce biological age."""
    lever_id: str
    title: str
    description: str
    potential_years_gained: float   # estimated years reduction in bio age
    difficulty: str                  # "easy" | "moderate" | "hard"
    timeframe: str                   # "weeks" | "months" | "years"
    component: str                   # associated component name

    def to_dict(self) -> dict:
        return {
            "lever_id": self.lever_id,
            "title": self.title,
            "description": self.description,
            "potential_years_gained": self.potential_years_gained,
            "difficulty": self.difficulty,
            "timeframe": self.timeframe,
            "component": self.component,
        }


@dataclass
class BiologicalAgeResult:
    """Complete biological age analysis result."""
    chronological_age: int
    biological_age: float
    biological_age_delta: float      # bio_age - chrono_age (negative = younger)
    longevity_risk_score: float      # 0-100 (higher = worse, = 100 - longevity_score proxy)
    components: list[BiologicalAgeComponent] = field(default_factory=list)
    levers: list[BiologicalAgeLever] = field(default_factory=list)
    trend_direction: str = "stable"  # "improving" | "stable" | "declining"
    confidence: float = 0.0          # proportion of components with real data (0-1)
    explanation: str = ""


# ── Metabolic age → score conversion ─────────────────────────────────────────

def _metabolic_age_to_score(
    metabolic_age: Optional[float],
    chronological_age: int,
) -> Optional[float]:
    """
    Convert metabolic age (years) to a 0-100 component score.

    Reference: score 75 → metabolic_age = chronological_age (no delta).
    metabolic_age 5 years younger → score 100.
    metabolic_age 5 years older → score 50.
    Clamped to [0, 100].
    """
    if metabolic_age is None:
        return None
    # Inverse of: bio_age = chrono - (score - 75) × 0.2
    # → score = 75 + (chrono - metabolic_age) / 0.2
    score = LONGEVITY_REFERENCE_SCORE + (chronological_age - metabolic_age) / YEARS_PER_SCORE_POINT
    return round(max(0.0, min(100.0, score)), 1)


# ── Component scoring helpers ─────────────────────────────────────────────────

def _make_component(
    factor_name: str,
    display_name: str,
    score: Optional[float],
    weight: float,
    explanation_ok: str,
    explanation_missing: str,
) -> BiologicalAgeComponent:
    """Create a BiologicalAgeComponent, handling missing data gracefully."""
    if score is None:
        return BiologicalAgeComponent(
            factor_name=factor_name,
            display_name=display_name,
            score=LONGEVITY_REFERENCE_SCORE,  # neutral when no data
            weight=weight,
            age_delta_years=0.0,
            explanation=explanation_missing,
            is_available=False,
        )
    age_delta = weight * (LONGEVITY_REFERENCE_SCORE - score) * YEARS_PER_SCORE_POINT
    return BiologicalAgeComponent(
        factor_name=factor_name,
        display_name=display_name,
        score=round(score, 1),
        weight=weight,
        age_delta_years=round(age_delta, 2),
        explanation=_explain_score(factor_name, score, explanation_ok),
        is_available=True,
    )


def _explain_score(factor_name: str, score: float, base: str) -> str:
    """Append a qualitative label to the base explanation."""
    if score >= 85:
        label = "excellent"
    elif score >= 70:
        label = "bon"
    elif score >= 55:
        label = "moyen"
    elif score >= 40:
        label = "faible"
    else:
        label = "très faible"
    return f"{base} (niveau {label} : {score:.0f}/100)"


# ── Component builders ────────────────────────────────────────────────────────

def _build_cardiovascular(cardio_score: Optional[float]) -> BiologicalAgeComponent:
    return _make_component(
        factor_name="cardiovascular",
        display_name="Santé cardiovasculaire",
        score=cardio_score,
        weight=COMPONENT_WEIGHTS["cardiovascular"],
        explanation_ok="Capacité cardio basée sur fréquence d'entraînement, HRV et activité quotidienne",
        explanation_missing="Données cardiovasculaires insuffisantes (HRV, pas, calories actives non disponibles)",
    )


def _build_metabolic(
    metabolic_age: Optional[float],
    chronological_age: int,
) -> BiologicalAgeComponent:
    score = _metabolic_age_to_score(metabolic_age, chronological_age)
    if score is None:
        explanation_ok = "Âge métabolique non calculé"
    else:
        delta = chronological_age - (metabolic_age or chronological_age)
        direction = "plus jeune" if delta >= 0 else "plus vieux"
        explanation_ok = (
            f"Âge métabolique {abs(delta):.1f} ans {direction} que l'âge chronologique"
        )
    return _make_component(
        factor_name="metabolic",
        display_name="Âge métabolique",
        score=score,
        weight=COMPONENT_WEIGHTS["metabolic"],
        explanation_ok=explanation_ok,
        explanation_missing="Jumeau métabolique non encore calculé (données BMR/TDEE manquantes)",
    )


def _build_body_composition(
    weight_score: Optional[float],
    body_comp_score: Optional[float],
) -> BiologicalAgeComponent:
    """Combine weight_score and body_comp_score if both available."""
    if weight_score is None and body_comp_score is None:
        score = None
    elif weight_score is None:
        score = body_comp_score
    elif body_comp_score is None:
        score = weight_score
    else:
        score = (weight_score + body_comp_score) / 2.0

    return _make_component(
        factor_name="body_composition",
        display_name="Composition corporelle",
        score=score,
        weight=COMPONENT_WEIGHTS["body_composition"],
        explanation_ok="IMC et composition corporelle évaluée",
        explanation_missing="Données de poids ou de composition corporelle manquantes",
    )


def _build_sleep(sleep_score: Optional[float]) -> BiologicalAgeComponent:
    return _make_component(
        factor_name="sleep",
        display_name="Qualité du sommeil",
        score=sleep_score,
        weight=COMPONENT_WEIGHTS["sleep"],
        explanation_ok="Durée et qualité du sommeil sur les 30 derniers jours",
        explanation_missing="Données de sommeil insuffisantes pour l'évaluation",
    )


def _build_activity(strength_score: Optional[float]) -> BiologicalAgeComponent:
    return _make_component(
        factor_name="activity",
        display_name="Activité physique et force",
        score=strength_score,
        weight=COMPONENT_WEIGHTS["activity"],
        explanation_ok="Volume d'entraînement et régularité des séances de force",
        explanation_missing="Aucune séance d'entraînement enregistrée récemment",
    )


def _build_recovery(readiness_score: Optional[float]) -> BiologicalAgeComponent:
    return _make_component(
        factor_name="recovery",
        display_name="Capacité de récupération",
        score=readiness_score,
        weight=COMPONENT_WEIGHTS["recovery"],
        explanation_ok="Score de préparation global intégrant sommeil, charge et bien-être",
        explanation_missing="Score de forme journalier non disponible",
    )


def _build_consistency(consistency_score: Optional[float]) -> BiologicalAgeComponent:
    return _make_component(
        factor_name="consistency",
        display_name="Régularité et suivi",
        score=consistency_score,
        weight=COMPONENT_WEIGHTS["consistency"],
        explanation_ok="Régularité du suivi santé et de l'activité sur 30 jours",
        explanation_missing="Données de régularité insuffisantes",
    )


# ── Lever generation ──────────────────────────────────────────────────────────

ALL_LEVERS: list[BiologicalAgeLever] = [
    BiologicalAgeLever(
        lever_id="improve_sleep",
        title="Améliorer la qualité du sommeil",
        description=(
            "Viser 7-9h de sommeil par nuit avec une heure de coucher régulière. "
            "Le sommeil profond est le levier de récupération cellulaire le plus puissant."
        ),
        potential_years_gained=2.5,
        difficulty="moderate",
        timeframe="weeks",
        component="sleep",
    ),
    BiologicalAgeLever(
        lever_id="increase_zone2_cardio",
        title="Augmenter le cardio en zone 2",
        description=(
            "Ajouter 150 min/semaine de cardio modéré (marche rapide, vélo, natation). "
            "Améliore la VO2max et le système cardiovasculaire — prédicteur majeur de longévité."
        ),
        potential_years_gained=3.0,
        difficulty="moderate",
        timeframe="months",
        component="cardiovascular",
    ),
    BiologicalAgeLever(
        lever_id="increase_strength_training",
        title="Renforcer la masse musculaire",
        description=(
            "2-3 séances de résistance par semaine. La masse musculaire protège contre "
            "le déclin métabolique et préserve l'autonomie à long terme."
        ),
        potential_years_gained=2.0,
        difficulty="moderate",
        timeframe="months",
        component="activity",
    ),
    BiologicalAgeLever(
        lever_id="improve_protein_intake",
        title="Optimiser l'apport protéique",
        description=(
            "Consommer 1.6-2.0 g de protéines/kg/jour. L'apport protéique adéquat "
            "maintient le métabolisme et préserve la masse maigre avec l'âge."
        ),
        potential_years_gained=1.5,
        difficulty="easy",
        timeframe="weeks",
        component="metabolic",
    ),
    BiologicalAgeLever(
        lever_id="reduce_fatigue",
        title="Réduire la charge de fatigue chronique",
        description=(
            "Intégrer des journées de décharge (deload) et respecter les signaux de récupération. "
            "La fatigue chronique accélère le vieillissement cellulaire (stress oxydatif)."
        ),
        potential_years_gained=1.8,
        difficulty="moderate",
        timeframe="weeks",
        component="recovery",
    ),
    BiologicalAgeLever(
        lever_id="improve_body_composition",
        title="Améliorer la composition corporelle",
        description=(
            "Réduire la masse grasse viscérale (cible IMC 20-24) via alimentation et "
            "entraînement combinés. Réduit inflammation chronique et risque métabolique."
        ),
        potential_years_gained=2.5,
        difficulty="hard",
        timeframe="months",
        component="body_composition",
    ),
    BiologicalAgeLever(
        lever_id="improve_consistency",
        title="Renforcer la régularité des habitudes santé",
        description=(
            "Maintenir un suivi quotidien et une activité régulière 4+j/semaine. "
            "La régularité est le meilleur prédicteur de résultats sur le long terme."
        ),
        potential_years_gained=1.2,
        difficulty="easy",
        timeframe="weeks",
        component="consistency",
    ),
]


def _select_levers(
    components: list[BiologicalAgeComponent],
) -> list[BiologicalAgeLever]:
    """Select and sort levers for components scoring below the trigger threshold."""
    score_by_factor = {c.factor_name: c.score for c in components if c.is_available}

    active_levers = []
    for lever in ALL_LEVERS:
        component_score = score_by_factor.get(lever.component)
        if component_score is not None and component_score < LEVER_TRIGGER_THRESHOLD:
            active_levers.append(lever)

    # Sort by potential years gained descending
    return sorted(active_levers, key=lambda l: l.potential_years_gained, reverse=True)


# ── Explanation builder ───────────────────────────────────────────────────────

def _build_explanation(
    biological_age: float,
    chronological_age: int,
    delta: float,
    confidence: float,
    primary_lever: Optional[BiologicalAgeLever],
) -> str:
    """Generate a human-readable overall explanation."""
    if confidence < 0.3:
        return (
            "Données insuffisantes pour calculer un âge biologique fiable. "
            "Enrichissez votre suivi (sommeil, activité, poids) pour une analyse précise."
        )

    if delta < -3:
        age_text = f"votre âge biologique estimé ({biological_age:.1f} ans) est significativement inférieur à votre âge chronologique ({chronological_age} ans)"
    elif delta < -0.5:
        age_text = f"votre âge biologique estimé ({biological_age:.1f} ans) est légèrement inférieur à votre âge chronologique ({chronological_age} ans)"
    elif delta <= 0.5:
        age_text = f"votre âge biologique ({biological_age:.1f} ans) correspond à votre âge chronologique ({chronological_age} ans)"
    elif delta <= 3:
        age_text = f"votre âge biologique estimé ({biological_age:.1f} ans) est légèrement supérieur à votre âge chronologique ({chronological_age} ans)"
    else:
        age_text = f"votre âge biologique estimé ({biological_age:.1f} ans) est significativement supérieur à votre âge chronologique ({chronological_age} ans)"

    lever_text = ""
    if primary_lever:
        lever_text = f" Priorité d'action : {primary_lever.title.lower()} ({primary_lever.potential_years_gained:.1f} ans potentiels)."

    return f"Avec une confiance de {confidence:.0%}, {age_text}.{lever_text}"


# ── Core compute function (pure) ──────────────────────────────────────────────

def compute_biological_age(
    chronological_age: int,
    # Longevity component scores (from LongevityScore model or longevity_engine)
    cardio_score: Optional[float] = None,
    strength_score: Optional[float] = None,
    sleep_score: Optional[float] = None,
    weight_score: Optional[float] = None,
    body_comp_score: Optional[float] = None,
    consistency_score: Optional[float] = None,
    # Metabolic Twin input
    metabolic_age: Optional[float] = None,
    # Recovery — new LOT 11 component
    readiness_score: Optional[float] = None,
    # Previous biological age delta (for trend calculation)
    prev_biological_age: Optional[float] = None,
) -> BiologicalAgeResult:
    """
    Compute biological age from available health data.

    Pure function — no DB access. All inputs are Optional; missing data
    results in neutral contribution (score=75, age_delta=0) but reduces confidence.

    Returns BiologicalAgeResult with full component breakdown and levers.
    """
    # Build all 7 components
    components = [
        _build_cardiovascular(cardio_score),
        _build_metabolic(metabolic_age, chronological_age),
        _build_body_composition(weight_score, body_comp_score),
        _build_sleep(sleep_score),
        _build_activity(strength_score),
        _build_recovery(readiness_score),
        _build_consistency(consistency_score),
    ]

    # Compute biological age = chrono + sum(component age deltas for available data only)
    available_weight_sum = sum(c.weight for c in components if c.is_available)
    confidence = round(available_weight_sum, 2)

    # Sum only available components' deltas; missing ones contribute 0
    total_delta = sum(c.age_delta_years for c in components if c.is_available)
    raw_bio_age = chronological_age + total_delta

    # Clamp to ±15 years from chronological age
    biological_age = round(
        max(chronological_age - BIO_AGE_CLAMP_YEARS,
            min(chronological_age + BIO_AGE_CLAMP_YEARS, raw_bio_age)),
        1,
    )
    biological_age_delta = round(biological_age - chronological_age, 1)

    # longevity_risk_score: inverse proxy (higher = worse)
    # Based on weighted average score of available components, inverted
    if available_weight_sum > 0:
        weighted_score = sum(
            c.score * c.weight for c in components if c.is_available
        ) / available_weight_sum
        longevity_risk_score = round(100 - weighted_score, 1)
    else:
        longevity_risk_score = 50.0

    # Trend direction (requires previous biological_age for comparison)
    trend_direction = "stable"
    if prev_biological_age is not None:
        prev_delta = prev_biological_age - chronological_age
        improvement = prev_delta - biological_age_delta  # positive = improving
        if improvement > 0.3:
            trend_direction = "improving"
        elif improvement < -0.3:
            trend_direction = "declining"

    # Levers
    levers = _select_levers(components)
    primary_lever = levers[0] if levers else None

    # Explanation
    explanation = _build_explanation(
        biological_age, chronological_age, biological_age_delta, confidence, primary_lever
    )

    return BiologicalAgeResult(
        chronological_age=chronological_age,
        biological_age=biological_age,
        biological_age_delta=biological_age_delta,
        longevity_risk_score=longevity_risk_score,
        components=components,
        levers=levers,
        trend_direction=trend_direction,
        confidence=confidence,
        explanation=explanation,
    )


# ── Persistence helpers ───────────────────────────────────────────────────────

async def save_biological_age(
    db: AsyncSession,
    user_id: uuid.UUID,
    result: BiologicalAgeResult,
    snapshot_date: Optional[date] = None,
) -> None:
    """Upsert BiologicalAgeSnapshot for today (or snapshot_date)."""
    from app.models.advanced import BiologicalAgeSnapshot

    snap_date = snapshot_date or date.today()

    stmt = pg_insert(BiologicalAgeSnapshot).values(
        user_id=user_id,
        snapshot_date=snap_date,
        chronological_age=result.chronological_age,
        biological_age=result.biological_age,
        biological_age_delta=result.biological_age_delta,
        longevity_risk_score=result.longevity_risk_score,
        components=[c.to_dict() for c in result.components],
        levers=[l.to_dict() for l in result.levers],
        trend_direction=result.trend_direction,
        confidence=result.confidence,
        explanation=result.explanation,
    ).on_conflict_do_update(
        constraint="uq_biological_age_user_date",
        set_={
            "chronological_age": result.chronological_age,
            "biological_age": result.biological_age,
            "biological_age_delta": result.biological_age_delta,
            "longevity_risk_score": result.longevity_risk_score,
            "components": [c.to_dict() for c in result.components],
            "levers": [l.to_dict() for l in result.levers],
            "trend_direction": result.trend_direction,
            "confidence": result.confidence,
            "explanation": result.explanation,
        },
    )
    await db.execute(stmt)
    await db.commit()


def build_bio_age_summary(result: BiologicalAgeResult) -> str:
    """Compact text for coach context builder."""
    top_lever = result.levers[0].title if result.levers else "Aucun"
    sign = "+" if result.biological_age_delta >= 0 else ""
    return (
        f"Âge biologique {result.biological_age:.1f} ans "
        f"(delta {sign}{result.biological_age_delta:.1f} ans, "
        f"trend: {result.trend_direction}). "
        f"Confiance: {result.confidence:.0%}. "
        f"Levier prioritaire: {top_lever}."
    )

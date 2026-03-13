"""
Digital Twin V2 — Physiological State Engine.

Différenciateurs vs MetabolicTwin V1 (metabolic_twin_service.py) :
- Chaque composante produit un TwinComponent (value, status, confidence, explanation, variables_used)
  → explainabilité totale pour le coach IA et l'UI Flutter.
- 3 nouvelles composantes : inflammation (proxy), sleep_debt (cumulatif), metabolic_flexibility (proxy).
- overall_status composite à 5 niveaux ("fresh" → "critical").
- primary_concern identifie le problème prioritaire.
- compute_digital_twin_state() est une fonction pure — zéro accès DB.
- save_digital_twin() et get_or_compute_digital_twin() gèrent la persistence async.

Architecture : même pattern que LOT 10 (dataclass + fonctions pures + helpers persistence).
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date
from statistics import mean, stdev
from typing import Optional

logger = logging.getLogger(__name__)

# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class TwinComponent:
    """
    A single physiological component with full explainability.
    Used for every dimension of the Digital Twin.
    """
    value: float                          # Numeric value (scale depends on component)
    status: str                           # Qualitative label (e.g., "tired", "depleted")
    confidence: float                     # 0-1 (based on data availability)
    explanation: str                      # Human-readable rationale
    variables_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "value": round(self.value, 2),
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "explanation": self.explanation,
            "variables_used": self.variables_used,
        }


@dataclass
class DigitalTwinState:
    """
    Complete physiological state snapshot for a user on a given day.
    All numeric values are Optional to handle missing data gracefully.
    """
    snapshot_date: date

    # ── Energy & Substrate ────────────────────────────────────────────────────
    energy_balance: TwinComponent         # kcal/day surplus or deficit
    glycogen: TwinComponent               # grams estimated (0-400g range)
    carb_availability: TwinComponent      # qualitative carb fuel status
    protein_status: TwinComponent         # adequacy ratio (consumed/needed)

    # ── Hydration ─────────────────────────────────────────────────────────────
    hydration: TwinComponent              # ml consumed vs target

    # ── Recovery dimensions ───────────────────────────────────────────────────
    fatigue: TwinComponent                # 0-100 (higher = more fatigued)
    inflammation: TwinComponent           # 0-100 proxy (training load + sleep quality)
    sleep_debt: TwinComponent             # min/night deficit average over 7d
    recovery_capacity: TwinComponent      # 0-100 (higher = better recovery potential)

    # ── Readiness ─────────────────────────────────────────────────────────────
    training_readiness: TwinComponent     # 0-100 (higher = ready for intense work)

    # ── Stress ────────────────────────────────────────────────────────────────
    stress_load: TwinComponent            # 0-100 (fatigue + sleep deficit + energy deficit)

    # ── Metabolic ─────────────────────────────────────────────────────────────
    metabolic_flexibility: TwinComponent  # 0-100 proxy (diet consistency + IF + weight trend)

    # ── Risk flags ────────────────────────────────────────────────────────────
    plateau_risk: bool = False
    under_recovery_risk: bool = False

    # ── Synthesis ─────────────────────────────────────────────────────────────
    overall_status: str = "moderate"   # fresh|good|moderate|tired|critical
    primary_concern: str = "none"
    global_confidence: float = 0.0
    recommendations: list[str] = field(default_factory=list)


# ── Status label helpers ───────────────────────────────────────────────────────

def _energy_status(balance_kcal: float) -> str:
    if balance_kcal >= 300: return "surplus"
    if balance_kcal >= -100: return "maintenance"
    if balance_kcal >= -400: return "deficit"
    return "large_deficit"

def _glycogen_status(g: float) -> str:
    if g < 80: return "depleted"
    if g < 180: return "low"
    if g < 320: return "normal"
    return "high"

def _fatigue_status(score: float) -> str:
    if score < 30: return "fresh"
    if score < 55: return "normal"
    if score < 75: return "tired"
    return "exhausted"

def _inflammation_status(score: float) -> str:
    if score < 25: return "low"
    if score < 50: return "moderate"
    if score < 75: return "elevated"
    return "high"

def _sleep_debt_status(min_per_night: float) -> str:
    if min_per_night < 10: return "none"
    if min_per_night < 30: return "mild"
    if min_per_night < 60: return "moderate"
    return "severe"

def _recovery_status(score: float) -> str:
    if score >= 80: return "excellent"
    if score >= 60: return "good"
    if score >= 40: return "limited"
    return "poor"

def _hydration_status(ratio: float) -> str:
    if ratio < 0.5: return "dehydrated"
    if ratio < 0.75: return "low"
    if ratio < 1.05: return "adequate"
    return "optimal"

def _readiness_status(score: float) -> str:
    if score >= 80: return "excellent"
    if score >= 65: return "good"
    if score >= 45: return "moderate"
    if score >= 25: return "low"
    return "very_low"

def _stress_status(score: float) -> str:
    if score < 25: return "low"
    if score < 50: return "moderate"
    if score < 75: return "high"
    return "critical"

def _flex_status(score: float) -> str:
    if score >= 75: return "high"
    if score >= 50: return "moderate"
    if score >= 25: return "low"
    return "very_low"


# ── Pure scoring functions ─────────────────────────────────────────────────────

def _score_energy_balance(
    calories_consumed: Optional[float],
    estimated_tdee: Optional[float],
) -> TwinComponent:
    """Compute daily energy balance (consumed - TDEE)."""
    if calories_consumed is None or estimated_tdee is None:
        return TwinComponent(
            value=0.0, status="unknown", confidence=0.0,
            explanation="Données caloriques ou TDEE manquantes.",
        )
    balance = calories_consumed - estimated_tdee
    return TwinComponent(
        value=round(balance, 1),
        status=_energy_status(balance),
        confidence=0.9,
        explanation=(
            f"Balance énergétique : {balance:+.0f} kcal/j "
            f"({calories_consumed:.0f} consommées − {estimated_tdee:.0f} TDEE estimé)."
        ),
        variables_used=["calories_consumed", "estimated_tdee"],
    )


def _score_glycogen(
    training_load_7d: Optional[float],
    carbs_g_avg: Optional[float],
    weight_kg: Optional[float],
) -> TwinComponent:
    """Estimate glycogen stores based on training load and carb intake."""
    if weight_kg is None:
        return TwinComponent(
            value=200.0, status="normal", confidence=0.1,
            explanation="Poids non disponible — estimation par défaut.",
        )
    # Max glycogen capacity ≈ 15 g/kg body weight (liver + muscle)
    max_glycogen = min(weight_kg * 15.0, 500.0)
    # Baseline: assume 50% full without data
    base = max_glycogen * 0.5
    confidence = 0.1
    vars_used: list[str] = []

    # Training depletion: each 100 training_load units depletes ~40g
    depletion = 0.0
    if training_load_7d is not None:
        depletion = (training_load_7d / 7.0) * 0.4  # daily depletion from avg
        confidence += 0.3
        vars_used.append("training_load_7d")

    # Carb replenishment: 1g carb ≈ 2.7g muscle glycogen (partial synthesis)
    replenishment = 0.0
    if carbs_g_avg is not None:
        replenishment = carbs_g_avg * 2.7 * 0.15  # 15% stored above baseline
        confidence += 0.4
        vars_used.append("carbs_g_avg")

    estimated = max(0.0, min(max_glycogen, base - depletion + replenishment))
    status = _glycogen_status(estimated)
    confidence = min(confidence, 1.0)
    if confidence < 0.2:
        confidence = 0.2
        vars_used.append("weight_kg")

    return TwinComponent(
        value=round(estimated, 1),
        status=status,
        confidence=round(confidence, 2),
        explanation=(
            f"Glycogène estimé : {estimated:.0f}g (max {max_glycogen:.0f}g). "
            f"Déplétion charge : {depletion:.0f}g, reconstitution glucides : {replenishment:.0f}g."
        ),
        variables_used=vars_used or ["weight_kg"],
    )


def _score_carb_availability(glycogen_status: str, carbs_g_avg: Optional[float]) -> TwinComponent:
    """Qualitative carb availability based on glycogen status and recent carb intake."""
    label_map = {
        "depleted": "very_low",
        "low": "low",
        "normal": "adequate",
        "high": "high",
        "unknown": "unknown",
    }
    avail = label_map.get(glycogen_status, "unknown")
    confidence = 0.5 if carbs_g_avg is None else 0.8
    carb_note = f", {carbs_g_avg:.0f}g glucides/j" if carbs_g_avg is not None else ""
    return TwinComponent(
        value={"very_low": 10, "low": 35, "adequate": 65, "high": 90, "unknown": 50}.get(avail, 50),
        status=avail,
        confidence=confidence,
        explanation=f"Disponibilité glucidique : {avail} (glycogène {glycogen_status}{carb_note}).",
        variables_used=["glycogen_status"] + (["carbs_g_avg"] if carbs_g_avg is not None else []),
    )


def _score_protein_status(
    protein_g: Optional[float],
    weight_kg: Optional[float],
    goal: Optional[str] = None,
) -> TwinComponent:
    """Protein adequacy based on consumed vs recommended (goal-adjusted)."""
    if protein_g is None or weight_kg is None:
        return TwinComponent(
            value=0.0, status="unknown", confidence=0.0,
            explanation="Protéines consommées ou poids non disponibles.",
        )
    # Target: 1.6 g/kg (maintenance/loss), 1.8 g/kg (gain), 2.0 g/kg (recovery)
    target_multiplier = {"muscle_gain": 1.8, "recovery": 2.0}.get(goal or "", 1.6)
    target = weight_kg * target_multiplier
    ratio = protein_g / target if target > 0 else 0.0
    if ratio >= 1.0: status = "adequate"
    elif ratio >= 0.75: status = "low"
    else: status = "insufficient"
    return TwinComponent(
        value=round(protein_g, 1),
        status=status,
        confidence=0.85,
        explanation=(
            f"Protéines : {protein_g:.0f}g / {target:.0f}g cible "
            f"({ratio * 100:.0f}% — objectif {target_multiplier}g/kg)."
        ),
        variables_used=["protein_g", "weight_kg"],
    )


def _score_hydration(
    hydration_ml: Optional[float],
    hydration_target_ml: Optional[float],
    weight_kg: Optional[float],
) -> TwinComponent:
    """Hydration status: consumed vs target (or estimated from weight)."""
    target = hydration_target_ml or (weight_kg * 35.0 if weight_kg else None)
    if hydration_ml is None or target is None:
        return TwinComponent(
            value=0.0, status="unknown", confidence=0.0,
            explanation="Hydratation non disponible.",
        )
    ratio = hydration_ml / target
    status = _hydration_status(ratio)
    confidence = 0.9 if hydration_target_ml is not None else 0.6
    return TwinComponent(
        value=round(hydration_ml, 0),
        status=status,
        confidence=confidence,
        explanation=(
            f"Hydratation : {hydration_ml:.0f}ml / {target:.0f}ml cible "
            f"({ratio * 100:.0f}%)."
        ),
        variables_used=["hydration_ml"] + (["hydration_target_ml"] if hydration_target_ml else ["weight_kg"]),
    )


def _score_fatigue(
    training_load_7d: Optional[float],
    sleep_score_avg: Optional[float],
    hrv_ms: Optional[float],
    resting_hr_bpm: Optional[float],
) -> TwinComponent:
    """
    Fatigue 0-100 (higher = more fatigued).
    Weights: training_load 40%, sleep 35%, HRV 15%, RHR 10%.
    """
    score = 0.0
    weight_sum = 0.0
    vars_used: list[str] = []

    if training_load_7d is not None:
        # load/7 per day; 200/day = 100% fatigue
        load_score = min(100.0, (training_load_7d / 7.0) / 2.0)
        score += load_score * 0.40
        weight_sum += 0.40
        vars_used.append("training_load_7d")

    if sleep_score_avg is not None:
        # Low sleep = high fatigue (inverse): 0 sleep_score = 100 fatigue
        sleep_fatigue = max(0.0, 100.0 - sleep_score_avg)
        score += sleep_fatigue * 0.35
        weight_sum += 0.35
        vars_used.append("sleep_score_avg")

    if hrv_ms is not None:
        # Low HRV = high fatigue: <30ms=100, 70ms+=0 (linear)
        hrv_fatigue = max(0.0, min(100.0, (70.0 - hrv_ms) / 0.70))
        score += hrv_fatigue * 0.15
        weight_sum += 0.15
        vars_used.append("hrv_ms")

    if resting_hr_bpm is not None:
        # High RHR = high fatigue: <50=0, >80=100
        rhr_fatigue = max(0.0, min(100.0, (resting_hr_bpm - 50.0) / 0.30))
        score += rhr_fatigue * 0.10
        weight_sum += 0.10
        vars_used.append("resting_hr_bpm")

    if weight_sum == 0.0:
        return TwinComponent(
            value=0.0, status="unknown", confidence=0.0,
            explanation="Aucune donnée de fatigue disponible.",
        )

    final_score = round(score / weight_sum, 1) if weight_sum < 1.0 else round(score, 1)
    return TwinComponent(
        value=final_score,
        status=_fatigue_status(final_score),
        confidence=round(weight_sum, 2),
        explanation=f"Fatigue : {final_score:.0f}/100 ({weight_sum * 100:.0f}% données disponibles).",
        variables_used=vars_used,
    )


def _score_inflammation(
    fatigue_value: Optional[float],
    sleep_score: Optional[float],
    acwr: Optional[float],
) -> TwinComponent:
    """
    Inflammation proxy 0-100 (higher = more inflamed).
    Formula: 0.50 × fatigue + 0.30 × (100 - sleep_score) + 0.20 × (ACWR excess × 30)
    ACWR excess = max(0, ACWR - 1.3) — above safe zone.
    """
    score = 0.0
    weight_sum = 0.0
    vars_used: list[str] = []

    if fatigue_value is not None:
        score += fatigue_value * 0.50
        weight_sum += 0.50
        vars_used.append("fatigue")

    if sleep_score is not None:
        score += (100.0 - sleep_score) * 0.30
        weight_sum += 0.30
        vars_used.append("sleep_score")

    if acwr is not None:
        acwr_excess = max(0.0, acwr - 1.3)
        score += min(100.0, acwr_excess * 30.0) * 0.20
        weight_sum += 0.20
        vars_used.append("acwr")

    if weight_sum == 0.0:
        return TwinComponent(
            value=0.0, status="low", confidence=0.0,
            explanation="Données insuffisantes — inflammation supposée faible.",
        )

    final = round(min(100.0, score / weight_sum if weight_sum < 1.0 else score), 1)
    return TwinComponent(
        value=final,
        status=_inflammation_status(final),
        confidence=round(weight_sum, 2),
        explanation=f"Inflammation estimée (proxy) : {final:.0f}/100.",
        variables_used=vars_used,
    )


def _score_sleep_debt(
    sleep_minutes_7d: Optional[list[float]],
    target_sleep_min: float = 480.0,  # 8h
) -> TwinComponent:
    """
    Sleep debt: average nightly deficit over the last 7 days.
    sleep_minutes_7d: list of actual sleep minutes per night (up to 7 values).
    """
    if not sleep_minutes_7d:
        return TwinComponent(
            value=0.0, status="unknown", confidence=0.0,
            explanation="Données de sommeil non disponibles.",
        )
    deficits = [max(0.0, target_sleep_min - m) for m in sleep_minutes_7d]
    avg_debt = mean(deficits) if deficits else 0.0
    confidence = min(1.0, len(sleep_minutes_7d) / 7.0)
    return TwinComponent(
        value=round(avg_debt, 1),
        status=_sleep_debt_status(avg_debt),
        confidence=round(confidence, 2),
        explanation=(
            f"Dette de sommeil : {avg_debt:.0f}min/nuit en déficit moyen "
            f"(cible {target_sleep_min:.0f}min, {len(sleep_minutes_7d)}j analysés)."
        ),
        variables_used=["sleep_minutes_7d"],
    )


def _score_recovery_capacity(
    readiness_score: Optional[float],
    sleep_debt_value: float,
    fatigue_value: float,
) -> TwinComponent:
    """
    Recovery capacity 0-100 (higher = more capable of recovering).
    Based on readiness, sleep debt, and current fatigue.
    """
    score = 0.0
    weight_sum = 0.0
    vars_used: list[str] = []

    if readiness_score is not None:
        score += readiness_score * 0.45
        weight_sum += 0.45
        vars_used.append("readiness_score")

    # Sleep debt penalty: 60min/night debt → 50% penalty
    sleep_capacity = max(0.0, 100.0 - (sleep_debt_value / 60.0) * 50.0)
    score += sleep_capacity * 0.30
    weight_sum += 0.30
    vars_used.append("sleep_debt")

    # Fatigue penalty (inverse)
    fatigue_capacity = max(0.0, 100.0 - fatigue_value)
    score += fatigue_capacity * 0.25
    weight_sum += 0.25
    vars_used.append("fatigue")

    final = round(score / weight_sum if weight_sum > 0 else 50.0, 1)
    return TwinComponent(
        value=final,
        status=_recovery_status(final),
        confidence=round(weight_sum, 2),
        explanation=f"Capacité de récupération : {final:.0f}/100.",
        variables_used=vars_used,
    )


def _score_training_readiness(
    recovery_capacity: float,
    fatigue_value: float,
    readiness_score: Optional[float],
) -> TwinComponent:
    """
    Training readiness 0-100 (higher = ready for intense training).
    Derived from recovery capacity and fatigue, modulated by readiness_score.
    """
    score = recovery_capacity * 0.50 + max(0.0, 100.0 - fatigue_value) * 0.30
    weight_sum = 0.80
    vars_used = ["recovery_capacity", "fatigue"]

    if readiness_score is not None:
        score += readiness_score * 0.20
        weight_sum += 0.20
        vars_used.append("readiness_score")

    final = round(score / weight_sum if weight_sum > 0 else 50.0, 1)
    return TwinComponent(
        value=final,
        status=_readiness_status(final),
        confidence=round(min(weight_sum, 1.0), 2),
        explanation=f"Prêt à l'entraînement : {final:.0f}/100.",
        variables_used=vars_used,
    )


def _score_stress_load(
    fatigue_value: float,
    sleep_debt_value: float,
    energy_balance_kcal: float,
) -> TwinComponent:
    """
    Stress load 0-100 (higher = more stressed).
    Combines fatigue, sleep debt, and energy deficit.
    """
    # Energy deficit stress (>300 deficit = significant stress)
    energy_stress = max(0.0, min(100.0, -energy_balance_kcal / 5.0))
    score = fatigue_value * 0.50 + min(100.0, sleep_debt_value) * 0.30 + energy_stress * 0.20
    final = round(min(100.0, score), 1)
    return TwinComponent(
        value=final,
        status=_stress_status(final),
        confidence=0.7,
        explanation=f"Charge de stress globale : {final:.0f}/100.",
        variables_used=["fatigue", "sleep_debt", "energy_balance"],
    )


def _score_metabolic_flexibility(
    has_if_protocol: bool,
    plateau_risk: bool,
    consistency_days: Optional[int],
    total_days: int = 7,
) -> TwinComponent:
    """
    Metabolic flexibility proxy 0-100.
    Higher = better ability to switch between fuel sources.
    Proxy: diet consistency + IF practice + no plateau.
    """
    score = 50.0  # baseline
    vars_used: list[str] = []

    if has_if_protocol:
        score += 20.0
        vars_used.append("if_protocol")

    if not plateau_risk:
        score += 15.0
    else:
        score -= 10.0
    vars_used.append("plateau_risk")

    if consistency_days is not None:
        consistency_ratio = consistency_days / total_days
        score += consistency_ratio * 15.0
        vars_used.append("consistency_days")

    final = round(max(0.0, min(100.0, score)), 1)
    confidence = 0.3 + (0.2 if has_if_protocol else 0) + (0.2 if consistency_days is not None else 0)
    return TwinComponent(
        value=final,
        status=_flex_status(final),
        confidence=round(min(confidence, 1.0), 2),
        explanation=f"Flexibilité métabolique (proxy) : {final:.0f}/100.",
        variables_used=vars_used,
    )


# ── Overall status ────────────────────────────────────────────────────────────

def _compute_overall_status(fatigue: float, recovery: float, readiness: float) -> str:
    """Synthesize overall status from key dimensions."""
    avg = (max(0.0, 100.0 - fatigue) + recovery + readiness) / 3.0
    if avg >= 85: return "fresh"
    if avg >= 70: return "good"
    if avg >= 50: return "moderate"
    if avg >= 30: return "tired"
    return "critical"


def _compute_primary_concern(state: dict[str, TwinComponent]) -> str:
    """Identify the component with the worst status as primary concern."""
    # Score each component by "badness"
    badness: dict[str, float] = {}

    bad_statuses = {
        "fatigue": {"exhausted": 100, "tired": 60, "normal": 20, "fresh": 0},
        "glycogen": {"depleted": 90, "low": 50, "normal": 10, "high": 0},
        "sleep_debt": {"severe": 90, "moderate": 60, "mild": 30, "none": 0, "unknown": 0},
        "inflammation": {"high": 90, "elevated": 60, "moderate": 30, "low": 0},
        "recovery_capacity": {"poor": 90, "limited": 60, "good": 20, "excellent": 0},
        "hydration": {"dehydrated": 90, "low": 50, "adequate": 10, "optimal": 0},
        "protein_status": {"insufficient": 80, "low": 40, "adequate": 0},
    }
    for key, comp in state.items():
        if key in bad_statuses:
            badness[key] = bad_statuses[key].get(comp.status, 0)

    if not badness or max(badness.values()) < 20:
        return "none"
    return max(badness, key=lambda k: badness[k])


def _generate_recommendations(
    overall_status: str,
    primary_concern: str,
    plateau_risk: bool,
    under_recovery: bool,
) -> list[str]:
    """Generate 1-3 actionable recommendations based on state."""
    recs: list[str] = []

    concern_recs = {
        "fatigue": "Priorisez le repos actif — évitez les séances intenses jusqu'à récupération.",
        "glycogen": "Augmentez l'apport en glucides complexes (riz, pâtes, patate douce) pour recharger les réserves.",
        "sleep_debt": "Visez 7-8h de sommeil consécutives — la dette de sommeil impacte récupération et performance.",
        "inflammation": "Réduisez la charge d'entraînement et privilégiez les aliments anti-inflammatoires (oméga-3, légumes colorés).",
        "recovery_capacity": "Ajoutez des techniques de récupération : étirements, mobilité, bain froid ou contraste.",
        "hydration": "Augmentez la consommation d'eau — visez votre cible hydrique avec des électrolytes si transpiration élevée.",
        "protein_status": "Augmentez l'apport protéique (œufs, poulet, légumineuses) pour atteindre votre cible journalière.",
        "none": "Votre état physiologique est équilibré — maintenez votre routine actuelle.",
    }

    recs.append(concern_recs.get(primary_concern, "Consultez votre coach pour des recommandations personnalisées."))

    if plateau_risk:
        recs.append("Plateau détecté : envisagez une semaine de décharge (deload) puis une recalibration calorique.")

    if under_recovery:
        recs.append("Sous-récupération détectée : ajoutez un jour de repos complet avant votre prochaine séance intense.")

    if overall_status == "critical":
        recs.insert(0, "⚠️ État critique : repos total recommandé aujourd'hui.")

    return recs[:3]


# ── Main compute function ──────────────────────────────────────────────────────

def compute_digital_twin_state(
    # Energy
    calories_consumed: Optional[float] = None,
    estimated_tdee: Optional[float] = None,
    # Macros
    carbs_g_avg: Optional[float] = None,
    protein_g: Optional[float] = None,
    # Hydration
    hydration_ml: Optional[float] = None,
    hydration_target_ml: Optional[float] = None,
    # Training
    training_load_7d: Optional[float] = None,
    acwr: Optional[float] = None,
    # Sleep
    sleep_score_avg: Optional[float] = None,
    sleep_minutes_7d: Optional[list[float]] = None,
    # Recovery
    hrv_ms: Optional[float] = None,
    resting_hr_bpm: Optional[float] = None,
    readiness_score: Optional[float] = None,
    # Body
    weight_kg: Optional[float] = None,
    goal: Optional[str] = None,
    # Metabolic flexibility context
    has_if_protocol: bool = False,
    plateau_risk: bool = False,
    consistency_days: Optional[int] = None,
    # Date
    target_date: Optional[date] = None,
) -> DigitalTwinState:
    """
    Compute a complete Digital Twin state from raw metrics.

    Pure function — no database access.
    All parameters are Optional; missing data reduces confidence scores.
    """
    from datetime import date as date_type
    snap_date = target_date or date_type.today()

    # 1. Compute each component
    energy = _score_energy_balance(calories_consumed, estimated_tdee)
    glycogen = _score_glycogen(training_load_7d, carbs_g_avg, weight_kg)
    carb_avail = _score_carb_availability(glycogen.status, carbs_g_avg)
    protein = _score_protein_status(protein_g, weight_kg, goal)
    hydration = _score_hydration(hydration_ml, hydration_target_ml, weight_kg)
    fatigue = _score_fatigue(training_load_7d, sleep_score_avg, hrv_ms, resting_hr_bpm)
    inflammation = _score_inflammation(
        fatigue.value if fatigue.confidence > 0 else None,
        sleep_score_avg,
        acwr,
    )
    sleep_debt = _score_sleep_debt(sleep_minutes_7d)
    recovery = _score_recovery_capacity(readiness_score, sleep_debt.value, fatigue.value)
    readiness_comp = _score_training_readiness(recovery.value, fatigue.value, readiness_score)
    stress = _score_stress_load(fatigue.value, sleep_debt.value, energy.value)
    flex = _score_metabolic_flexibility(has_if_protocol, plateau_risk, consistency_days)

    # 2. Risk flags
    under_recovery = (
        recovery.value < 40 and fatigue.value > 65 and sleep_debt.value > 30
    )

    # 3. Overall synthesis
    overall_status = _compute_overall_status(fatigue.value, recovery.value, readiness_comp.value)

    # 4. Primary concern
    component_map = {
        "fatigue": fatigue, "glycogen": glycogen,
        "sleep_debt": sleep_debt, "inflammation": inflammation,
        "recovery_capacity": recovery, "hydration": hydration,
        "protein_status": protein,
    }
    primary_concern = _compute_primary_concern(component_map)

    # 5. Global confidence (average of all component confidences)
    all_confidences = [
        energy.confidence, glycogen.confidence, carb_avail.confidence,
        protein.confidence, hydration.confidence, fatigue.confidence,
        inflammation.confidence, sleep_debt.confidence, recovery.confidence,
        readiness_comp.confidence, stress.confidence, flex.confidence,
    ]
    global_confidence = round(mean(all_confidences), 3)

    # 6. Recommendations
    recs = _generate_recommendations(overall_status, primary_concern, plateau_risk, under_recovery)

    return DigitalTwinState(
        snapshot_date=snap_date,
        energy_balance=energy,
        glycogen=glycogen,
        carb_availability=carb_avail,
        protein_status=protein,
        hydration=hydration,
        fatigue=fatigue,
        inflammation=inflammation,
        sleep_debt=sleep_debt,
        recovery_capacity=recovery,
        training_readiness=readiness_comp,
        stress_load=stress,
        metabolic_flexibility=flex,
        plateau_risk=plateau_risk,
        under_recovery_risk=under_recovery,
        overall_status=overall_status,
        primary_concern=primary_concern,
        global_confidence=global_confidence,
        recommendations=recs,
    )


# ── Persistence helpers ───────────────────────────────────────────────────────

async def save_digital_twin(
    db,
    user_id: uuid.UUID,
    state: DigitalTwinState,
) -> None:
    """Upsert a DigitalTwinSnapshot from a computed DigitalTwinState."""
    from sqlalchemy import select
    from sqlalchemy.dialects.postgresql import insert
    from app.models.advanced import DigitalTwinSnapshot

    components_dict = {
        "energy_balance": state.energy_balance.to_dict(),
        "glycogen": state.glycogen.to_dict(),
        "carb_availability": state.carb_availability.to_dict(),
        "protein_status": state.protein_status.to_dict(),
        "hydration": state.hydration.to_dict(),
        "fatigue": state.fatigue.to_dict(),
        "inflammation": state.inflammation.to_dict(),
        "sleep_debt": state.sleep_debt.to_dict(),
        "recovery_capacity": state.recovery_capacity.to_dict(),
        "training_readiness": state.training_readiness.to_dict(),
        "stress_load": state.stress_load.to_dict(),
        "metabolic_flexibility": state.metabolic_flexibility.to_dict(),
    }

    stmt = (
        insert(DigitalTwinSnapshot)
        .values(
            id=uuid.uuid4(),
            user_id=user_id,
            snapshot_date=state.snapshot_date,
            components=components_dict,
            overall_status=state.overall_status,
            primary_concern=state.primary_concern,
            global_confidence=state.global_confidence,
            plateau_risk=state.plateau_risk,
            under_recovery_risk=state.under_recovery_risk,
            recommendations=state.recommendations,
        )
        .on_conflict_do_update(
            constraint="uq_digital_twin_user_date",
            set_={
                "components": components_dict,
                "overall_status": state.overall_status,
                "primary_concern": state.primary_concern,
                "global_confidence": state.global_confidence,
                "plateau_risk": state.plateau_risk,
                "under_recovery_risk": state.under_recovery_risk,
                "recommendations": state.recommendations,
            },
        )
    )
    await db.execute(stmt)
    await db.commit()
    logger.debug("Digital Twin saved for user %s on %s", user_id, state.snapshot_date)


async def get_digital_twin_snapshot(db, user_id: uuid.UUID, target_date: date):
    """Return the latest DigitalTwinSnapshot for user on or before target_date."""
    from sqlalchemy import select
    from app.models.advanced import DigitalTwinSnapshot

    result = await db.execute(
        select(DigitalTwinSnapshot)
        .where(
            DigitalTwinSnapshot.user_id == user_id,
            DigitalTwinSnapshot.snapshot_date <= target_date,
        )
        .order_by(DigitalTwinSnapshot.snapshot_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def build_twin_summary(state: DigitalTwinState) -> str:
    """
    Build a concise text summary of the Digital Twin state for the coach context.
    Kept under 300 chars for token budget.
    """
    flags = []
    if state.plateau_risk:
        flags.append("plateau")
    if state.under_recovery_risk:
        flags.append("sous-récupération")

    flag_str = f" ⚠️ {', '.join(flags)}" if flags else ""
    primary = state.primary_concern.replace("_", " ") if state.primary_concern != "none" else "aucun"

    return (
        f"Jumeau {state.overall_status.upper()} | "
        f"Readiness {state.training_readiness.value:.0f}/100 | "
        f"Fatigue {state.fatigue.value:.0f}/100 | "
        f"Glycogène {state.glycogen.status} | "
        f"Problème prioritaire : {primary}{flag_str}"
    )

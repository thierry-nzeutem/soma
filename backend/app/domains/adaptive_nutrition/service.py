"""
Adaptive Nutrition Engine — LOT 11.

Determines the type of day (REST/TRAINING/INTENSE_TRAINING/RECOVERY/DELOAD)
and computes individualized macro targets with rationale and priority.

Stateless engine — no DB writes. Results are computed on demand.

Decision rules:
  INTENSE_TRAINING : training_load_today >= 100 AND readiness >= 70
  TRAINING         : training_load_today >= 50
  RECOVERY         : readiness <= 40 OR fatigue >= 75
  DELOAD           : ACWR > 1.5 (chronic overload trend)
  REST             : default

Calorie targets:
  Base  = TDEE + goal_delta (-300 loss / 0 maintain / +300 gain)
  INTENSE_TRAINING  → +300 kcal
  RECOVERY          → -150 kcal (but not below maintenance)
  DELOAD            → maintenance (ignores goal delta)
  Fatigue > 75      → reduce deficit by 150 kcal
  Plateau active    → switch to maintenance

Protein targets (g/kg body weight):
  REST=1.6, TRAINING=1.8, INTENSE=2.0, RECOVERY=2.2

Carb targets (g/kg):
  REST=2.5, TRAINING=4.0, INTENSE=5.5, RECOVERY=3.0
  Glycogen depleted  → +0.5 g/kg bonus

Fat target: remaining calories (min 0.7 g/kg, max 1.5 g/kg)

Hydration (ml): weight_kg × 35 + TRAINING:+500 + INTENSE:+1000

Fasting compatibility:
  NOT compatible if glycogen=depleted AND training day
  NOT compatible if fatigue > 70
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

# ── Day type ──────────────────────────────────────────────────────────────────

class DayType(str, Enum):
    REST = "rest"
    TRAINING = "training"
    INTENSE_TRAINING = "intense_training"
    RECOVERY = "recovery"
    DELOAD = "deload"


DAY_TYPE_LABELS: dict[str, str] = {
    DayType.REST: "Jour de repos",
    DayType.TRAINING: "Jour d'entraînement",
    DayType.INTENSE_TRAINING: "Entraînement intense",
    DayType.RECOVERY: "Jour de récupération",
    DayType.DELOAD: "Semaine de décharge",
}

_TRAINING_DAYS = {DayType.TRAINING, DayType.INTENSE_TRAINING}


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class NutritionTarget:
    """A single macro/hydration target with adaptive rationale."""
    value: float
    unit: str
    rationale: str
    priority: str  # "critical" | "high" | "normal" | "low"

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "unit": self.unit,
            "rationale": self.rationale,
            "priority": self.priority,
        }


@dataclass
class AdaptiveNutritionPlan:
    """Complete adaptive nutrition plan for a given day."""
    target_date: date
    day_type: DayType
    glycogen_status: str                        # "depleted"|"low"|"normal"|"high"|"unknown"

    # Macros
    calorie_target: NutritionTarget
    protein_target: NutritionTarget
    carb_target: NutritionTarget
    fat_target: NutritionTarget
    fiber_target: NutritionTarget
    hydration_target: NutritionTarget

    # Strategies and guidance
    meal_timing_strategy: str
    fasting_compatible: bool
    fasting_rationale: str
    pre_workout_guidance: Optional[str]
    post_workout_guidance: Optional[str]
    recovery_nutrition_focus: str
    electrolyte_focus: str
    supplementation_focus: list[str] = field(default_factory=list)

    # Meta
    confidence: float = 0.0
    assumptions: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


# ── Day type determination ────────────────────────────────────────────────────

def _determine_day_type(
    training_load_today: Optional[float],
    readiness_score: Optional[float],
    fatigue_score: Optional[float],
    acwr: Optional[float],
    day_type_hint: Optional[str] = None,
) -> DayType:
    """
    Determine the nutritional day type from physiological signals.

    Priority order: RECOVERY > DELOAD > INTENSE_TRAINING > TRAINING > REST.
    If day_type_hint is provided (and valid), it overrides the computed type.
    """
    # Allow explicit override (e.g. from user or test)
    if day_type_hint:
        try:
            return DayType(day_type_hint)
        except ValueError:
            pass

    load = training_load_today or 0.0
    readiness = readiness_score or 50.0
    fatigue = fatigue_score or 0.0

    # RECOVERY first: low readiness or high fatigue
    if readiness <= 40 or fatigue >= 75:
        return DayType.RECOVERY

    # DELOAD: chronic overload (ACWR > 1.5)
    if acwr is not None and acwr > 1.5:
        return DayType.DELOAD

    # INTENSE_TRAINING: heavy load with good readiness
    if load >= 100 and readiness >= 70:
        return DayType.INTENSE_TRAINING

    # TRAINING: moderate load
    if load >= 50:
        return DayType.TRAINING

    return DayType.REST


# ── Calorie target ────────────────────────────────────────────────────────────

def _compute_calorie_target(
    tdee: Optional[float],
    goal: Optional[str],
    day_type: DayType,
    fatigue_score: Optional[float],
    plateau_risk: bool,
    weight_kg: Optional[float],
) -> NutritionTarget:
    """Compute calorie target with day-type and context adjustments."""
    base_tdee = tdee or (weight_kg * 30 if weight_kg else 2000.0)

    # Goal delta
    if plateau_risk:
        goal_delta = 0  # Switch to maintenance if plateau
        plateau_note = " Plateau détecté : cible de maintien."
    elif goal == "weight_loss":
        goal_delta = -300
        plateau_note = ""
    elif goal == "muscle_gain":
        goal_delta = 300
        plateau_note = ""
    else:
        goal_delta = 0
        plateau_note = ""

    base = base_tdee + goal_delta

    # Day-type adjustment
    if day_type == DayType.INTENSE_TRAINING:
        adjustment = 300
        rationale_suffix = " +300 kcal pour soutenir l'entraînement intense."
        priority = "high"
    elif day_type == DayType.RECOVERY:
        adjustment = -150
        rationale_suffix = " -150 kcal : journée de récupération."
        priority = "normal"
    elif day_type == DayType.DELOAD:
        # Deload → maintenance regardless of goal
        base = base_tdee
        adjustment = 0
        rationale_suffix = " Semaine de décharge : retour à la maintenance."
        priority = "normal"
    else:
        adjustment = 0
        rationale_suffix = ""
        priority = "normal"

    # Reduce deficit when fatigued
    fatigue_correction = 0
    if (fatigue_score or 0) > 75 and goal_delta < 0:
        fatigue_correction = 150
        rationale_suffix += " Fatigue élevée : déficit réduit de 150 kcal."

    target_kcal = round(max(1200.0, base + adjustment + fatigue_correction), 0)

    rationale = (
        f"TDEE estimé {base_tdee:.0f} kcal"
        f"{plateau_note}"
        f"{rationale_suffix}"
    )

    return NutritionTarget(
        value=target_kcal,
        unit="kcal",
        rationale=rationale,
        priority=priority,
    )


# ── Macro targets ─────────────────────────────────────────────────────────────

# Protein g/kg by day type
_PROTEIN_MULTIPLIERS: dict[DayType, float] = {
    DayType.REST:             1.6,
    DayType.TRAINING:         1.8,
    DayType.INTENSE_TRAINING: 2.0,
    DayType.RECOVERY:         2.2,
    DayType.DELOAD:           1.7,
}

# Carb g/kg by day type
_CARB_MULTIPLIERS: dict[DayType, float] = {
    DayType.REST:             2.5,
    DayType.TRAINING:         4.0,
    DayType.INTENSE_TRAINING: 5.5,
    DayType.RECOVERY:         3.0,
    DayType.DELOAD:           3.0,
}


def _compute_protein_target(
    weight_kg: Optional[float],
    day_type: DayType,
) -> NutritionTarget:
    kg = weight_kg or 70.0
    multiplier = _PROTEIN_MULTIPLIERS[day_type]
    g = round(kg * multiplier, 0)
    priority = "critical" if day_type == DayType.RECOVERY else "high"
    return NutritionTarget(
        value=g,
        unit="g",
        rationale=(
            f"{multiplier} g/kg pour {DAY_TYPE_LABELS.get(day_type, day_type)} "
            f"({kg:.0f} kg × {multiplier})"
        ),
        priority=priority,
    )


def _compute_carb_target(
    weight_kg: Optional[float],
    day_type: DayType,
    glycogen_status: str,
) -> NutritionTarget:
    kg = weight_kg or 70.0
    multiplier = _CARB_MULTIPLIERS[day_type]
    bonus = 0.5 if glycogen_status == "depleted" else 0.0
    effective_multiplier = multiplier + bonus
    g = round(kg * effective_multiplier, 0)

    rationale = (
        f"{multiplier} g/kg (type {DAY_TYPE_LABELS.get(day_type, day_type)})"
    )
    if bonus > 0:
        rationale += " +0.5 g/kg bonus glycogène bas"

    priority = "high" if day_type in _TRAINING_DAYS else "normal"
    return NutritionTarget(
        value=g,
        unit="g",
        rationale=rationale,
        priority=priority,
    )


def _compute_fat_target(
    calorie_target: float,
    protein_g: float,
    carb_g: float,
    weight_kg: Optional[float],
) -> NutritionTarget:
    kg = weight_kg or 70.0
    calories_from_protein = protein_g * 4
    calories_from_carbs = carb_g * 4
    remaining_calories = calorie_target - calories_from_protein - calories_from_carbs
    fat_g_raw = remaining_calories / 9.0

    # Clamp: min 0.7 g/kg, max 1.5 g/kg
    fat_g = round(max(kg * 0.7, min(kg * 1.5, fat_g_raw)), 0)

    return NutritionTarget(
        value=fat_g,
        unit="g",
        rationale=(
            f"Calories restantes ({remaining_calories:.0f} kcal) / 9, "
            f"corrigé entre {0.7:.1f}-{1.5:.1f} g/kg"
        ),
        priority="normal",
    )


def _compute_fiber_target(calorie_target: float) -> NutritionTarget:
    """14 g fiber per 1000 kcal (American Dietetic Association reference)."""
    g = round((calorie_target / 1000) * 14, 0)
    return NutritionTarget(
        value=g,
        unit="g",
        rationale=f"14 g/1000 kcal ({calorie_target:.0f} kcal cible)",
        priority="low",
    )


def _compute_hydration_target(
    weight_kg: Optional[float],
    day_type: DayType,
) -> NutritionTarget:
    kg = weight_kg or 70.0
    base_ml = kg * 35

    if day_type == DayType.INTENSE_TRAINING:
        extra = 1000
        extra_note = " +1000 ml entraînement intense"
    elif day_type in _TRAINING_DAYS:
        extra = 500
        extra_note = " +500 ml entraînement"
    else:
        extra = 0
        extra_note = ""

    target_ml = round(base_ml + extra, 0)
    return NutritionTarget(
        value=target_ml,
        unit="ml",
        rationale=f"{kg:.0f} kg × 35 ml{extra_note}",
        priority="high",
    )


# ── Strategies and guidance ───────────────────────────────────────────────────

def _meal_timing_strategy(day_type: DayType, fasting_compatible: bool) -> str:
    if fasting_compatible:
        return "Fenêtre alimentaire 16:8 compatible — privilégier repas autour des entraînements"
    strategies = {
        DayType.REST:             "3 repas équilibrés, pas de collation nécessaire",
        DayType.TRAINING:         "3 repas + collation pré/post entraînement (30-60 min avant/après)",
        DayType.INTENSE_TRAINING: "4 prises alimentaires — petit déjeuner riche, repas pré-training 2h avant, récupération dans les 30 min, dîner protéiné",
        DayType.RECOVERY:         "3 repas légers à digestion facile — priorité aux aliments anti-inflammatoires",
        DayType.DELOAD:           "3 repas normaux, réduction glucides — focus légumes et protéines",
    }
    return strategies.get(day_type, "3 repas équilibrés")


def _pre_workout_guidance(day_type: DayType) -> Optional[str]:
    if day_type == DayType.INTENSE_TRAINING:
        return (
            "2h avant : repas mixte glucides complexes + protéines (ex: riz + poulet). "
            "30 min avant : banane ou gel énergétique si besoin."
        )
    if day_type == DayType.TRAINING:
        return (
            "1-2h avant : snack glucidique léger (ex: fruit + yaourt). "
            "Éviter les aliments gras ou riches en fibres."
        )
    return None


def _post_workout_guidance(day_type: DayType) -> Optional[str]:
    if day_type in _TRAINING_DAYS:
        return (
            "Dans les 30-60 min : 25-40 g de protéines + glucides rapides (ratio 1:3). "
            "Ex: shake protéiné + banane, ou œufs + pain complet."
        )
    return None


def _recovery_focus(day_type: DayType, glycogen_status: str) -> str:
    if day_type == DayType.RECOVERY:
        return "Anti-inflammatoires (oméga-3, curcumine, baies), magnésium, vitamine C"
    if glycogen_status == "depleted":
        return "Recharge glycogénique prioritaire — glucides complexes à chaque repas"
    if day_type == DayType.DELOAD:
        return "Récupération active — protéines + micronutriments, réduction charge glucidique"
    return "Maintenance habituelle — diversité alimentaire pour micronutriments"


def _electrolyte_focus(day_type: DayType) -> str:
    if day_type == DayType.INTENSE_TRAINING:
        return "Sodium (400-700 mg/L sueur), potassium, magnésium — boisson isotonique recommandée"
    if day_type == DayType.TRAINING:
        return "Hydratation suffisante + pincée de sel si transpiration importante"
    return "Hydratation normale — eau plate suffisante"


def _supplementation_focus(
    day_type: DayType,
    glycogen_status: str,
    readiness_score: Optional[float],
) -> list[str]:
    supplements = []
    if day_type in _TRAINING_DAYS:
        supplements.append("Créatine 3-5 g (si protocole en cours)")
    if day_type == DayType.INTENSE_TRAINING:
        supplements.append("Caféine 3-6 mg/kg (si tolérance) 60 min avant")
    if day_type == DayType.RECOVERY:
        supplements.append("Magnésium glycinate 300-400 mg (soir)")
        supplements.append("Oméga-3 2-3 g EPA+DHA")
    if glycogen_status == "depleted" and day_type in _TRAINING_DAYS:
        supplements.append("Maltodextrine ou BCAA intra-entraînement")
    if readiness_score is not None and readiness_score < 50:
        supplements.append("Ashwagandha 300-600 mg (adaptogène récupération)")
    return supplements


def _fasting_compatible(
    day_type: DayType,
    glycogen_status: str,
    fatigue_score: Optional[float],
    has_if_protocol: bool,
) -> tuple[bool, str]:
    """Determine if intermittent fasting is compatible with today's context."""
    if not has_if_protocol:
        return False, "Pas de protocole jeûne intermittent configuré"

    fatigue = fatigue_score or 0.0

    if glycogen_status == "depleted" and day_type in _TRAINING_DAYS:
        return False, "Glycogène bas + entraînement : fenêtre alimentaire élargie nécessaire"

    if fatigue > 70:
        return (
            False,
            f"Fatigue élevée ({fatigue:.0f}/100) : jeûne contre-indiqué — prioriser la récupération nutritionnelle",
        )

    if day_type == DayType.INTENSE_TRAINING:
        return False, "Entraînement intense : alimentation pré-training obligatoire"

    if day_type == DayType.RECOVERY:
        return True, "Récupération légère compatible avec fenêtre 14:10"

    return True, "Profil compatible avec protocole 16:8"


# ── Confidence computation ────────────────────────────────────────────────────

def _compute_confidence(
    tdee: Optional[float],
    weight_kg: Optional[float],
    readiness_score: Optional[float],
    training_load_today: Optional[float],
) -> tuple[float, list[str]]:
    """
    Compute confidence score (0-1) and list assumptions.
    """
    available = 0
    total = 4
    assumptions = []

    if tdee is not None:
        available += 1
    else:
        assumptions.append("TDEE estimé depuis poids (calcul approché)")

    if weight_kg is not None:
        available += 1
    else:
        assumptions.append("Poids par défaut 70 kg — renseignez votre profil pour précision")

    if readiness_score is not None:
        available += 1
    else:
        assumptions.append("Score de forme absent — type de journée estimé depuis charge")

    if training_load_today is not None:
        available += 1
    else:
        assumptions.append("Charge du jour inconnue — type de journée par défaut REST")

    return round(available / total, 2), assumptions


# ── Core compute function (pure) ──────────────────────────────────────────────

def compute_adaptive_plan(
    target_date: Optional[date] = None,
    # Day type inputs
    training_load_today: Optional[float] = None,
    readiness_score: Optional[float] = None,
    fatigue_score: Optional[float] = None,
    acwr: Optional[float] = None,
    day_type_hint: Optional[str] = None,
    # Nutrition inputs
    tdee: Optional[float] = None,
    goal: Optional[str] = None,
    weight_kg: Optional[float] = None,
    glycogen_status: str = "unknown",
    plateau_risk: bool = False,
    has_if_protocol: bool = False,
) -> AdaptiveNutritionPlan:
    """
    Compute an adaptive nutrition plan for the given day.

    Pure function — no DB access.
    All inputs are Optional; sensible defaults are used when data is missing.
    """
    plan_date = target_date or date.today()

    # Determine day type
    day_type = _determine_day_type(
        training_load_today, readiness_score, fatigue_score, acwr, day_type_hint
    )

    # Compute macros
    calorie_target = _compute_calorie_target(
        tdee, goal, day_type, fatigue_score, plateau_risk, weight_kg
    )
    protein_target = _compute_protein_target(weight_kg, day_type)
    carb_target = _compute_carb_target(weight_kg, day_type, glycogen_status)
    fat_target = _compute_fat_target(
        calorie_target.value, protein_target.value, carb_target.value, weight_kg
    )
    fiber_target = _compute_fiber_target(calorie_target.value)
    hydration_target = _compute_hydration_target(weight_kg, day_type)

    # Fasting compatibility
    fasting_ok, fasting_rationale = _fasting_compatible(
        day_type, glycogen_status, fatigue_score, has_if_protocol
    )

    # Guidance
    pre_workout = _pre_workout_guidance(day_type)
    post_workout = _post_workout_guidance(day_type)
    meal_timing = _meal_timing_strategy(day_type, fasting_ok)
    recovery_focus = _recovery_focus(day_type, glycogen_status)
    electrolyte = _electrolyte_focus(day_type)
    supplementation = _supplementation_focus(day_type, glycogen_status, readiness_score)

    # Confidence and assumptions
    confidence, assumptions = _compute_confidence(
        tdee, weight_kg, readiness_score, training_load_today
    )

    # Alerts
    alerts: list[str] = []
    if glycogen_status == "depleted" and day_type in _TRAINING_DAYS:
        alerts.append("⚠️ Glycogène bas : performance réduite — glucides prioritaires ce soir")
    if (fatigue_score or 0) > 80:
        alerts.append("⚠️ Fatigue critique : envisager une journée de récupération complète")
    if plateau_risk and goal == "weight_loss":
        alerts.append("⚠️ Plateau détecté : passage temporaire à la maintenance calorique")
    if acwr is not None and acwr > 1.8:
        alerts.append(f"⚠️ ACWR = {acwr:.2f} : risque de surentraînement — réduire intensité")

    return AdaptiveNutritionPlan(
        target_date=plan_date,
        day_type=day_type,
        glycogen_status=glycogen_status,
        calorie_target=calorie_target,
        protein_target=protein_target,
        carb_target=carb_target,
        fat_target=fat_target,
        fiber_target=fiber_target,
        hydration_target=hydration_target,
        meal_timing_strategy=meal_timing,
        fasting_compatible=fasting_ok,
        fasting_rationale=fasting_rationale,
        pre_workout_guidance=pre_workout,
        post_workout_guidance=post_workout,
        recovery_nutrition_focus=recovery_focus,
        electrolyte_focus=electrolyte,
        supplementation_focus=supplementation,
        confidence=confidence,
        assumptions=assumptions,
        alerts=alerts,
    )


def build_adaptive_nutrition_summary(plan: AdaptiveNutritionPlan) -> str:
    """Compact text for coach context builder."""
    return (
        f"Type de jour : {DAY_TYPE_LABELS.get(plan.day_type, plan.day_type)}. "
        f"Cible : {plan.calorie_target.value:.0f} kcal, "
        f"prot {plan.protein_target.value:.0f} g, "
        f"gluc {plan.carb_target.value:.0f} g, "
        f"lip {plan.fat_target.value:.0f} g. "
        f"Hydratation : {plan.hydration_target.value:.0f} ml. "
        f"Jeûne : {'compatible' if plan.fasting_compatible else 'non recommandé'}."
    )

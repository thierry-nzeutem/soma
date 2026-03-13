"""
SOMA LOT 13 - Personalized Learning Engine.

Analyzes user history to compute personalized physiological coefficients:
- true_tdee: Real Total Daily Energy Expenditure (from weight + calorie history)
- metabolic_efficiency: Ratio true_tdee / mifflin_tdee (slow=<0.95, fast=>1.05)
- recovery_profile: "fast"|"normal"|"slow" (days to recover post hard training)
- recovery_factor: float 0.5-1.5 (multiplier for recovery capacity)
- training_load_tolerance: float (weekly ATL user can sustain, in arbitrary load units)
- carb_response: float -1 to +1 (positive = better readiness on high-carb days)
- protein_response: float -1 to +1 (positive = better body composition with high protein)
- sleep_recovery_factor: float 0.5-1.5 (quality of sleep for recovery)
- adaptation_rate: float 0-1 (how quickly user adapts to training stress)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from statistics import mean, stdev
from typing import Optional

logger = logging.getLogger(__name__)

# --- Constants ----------------------------------------------------------------

KCAL_PER_KG_FAT = 7700.0          # kcal per kg of body fat
MIN_DAYS_FOR_TDEE = 14             # minimum history for TDEE estimation
MIN_DAYS_FOR_CARB_RESPONSE = 7     # minimum for carb/protein response
MIN_SESSIONS_FOR_TOLERANCE = 10    # minimum training sessions for tolerance
REFERENCE_EFFICIENCY = 1.0         # neutral metabolic efficiency

# Recovery thresholds
FAST_RECOVERY_THRESHOLD = 75.0     # readiness > 75 within 24h post training
NORMAL_RECOVERY_THRESHOLD = 60.0   # readiness > 60 within 48h
HARD_SESSION_THRESHOLD = 70.0      # training load defining a "hard" session


# --- Data structures ----------------------------------------------------------

@dataclass
class WeightCalorieObservation:
    """Single day observation for TDEE estimation."""
    obs_date: date
    weight_kg: float
    calories_consumed: float


@dataclass
class ReadinessObservation:
    """Readiness score with optional prior training load."""
    obs_date: date
    readiness_score: float
    prior_training_load: Optional[float] = None  # training load from previous day


@dataclass
class TrainingObservation:
    """Training session for load tolerance analysis."""
    session_date: date
    training_load: float                          # arbitrary load units (e.g. RPE x duration)
    acwr: Optional[float] = None                  # acute:chronic workload ratio
    fatigue_score: Optional[float] = None         # 0-100 fatigue after session


@dataclass
class NutritionReadinessObservation:
    """Nutrition intake paired with next-day readiness for response analysis."""
    obs_date: date
    carbs_g: float
    protein_g: float
    weight_kg: float
    next_day_readiness: Optional[float] = None    # readiness score the following day


@dataclass
class UserLearningResult:
    """
    Personalized physiological profile learned from history.
    All fields have fallback defaults when data is insufficient.
    """
    # TDEE & Metabolism
    true_tdee: Optional[float]                    # Real TDEE in kcal/day
    estimated_mifflin_tdee: Optional[float]       # Mifflin-St Jeor baseline
    metabolic_efficiency: float                   # true/mifflin ratio (1.0 = reference)
    metabolic_trend: str                          # "improving"|"stable"|"declining"

    # Recovery
    recovery_profile: str                         # "fast"|"normal"|"slow"
    recovery_factor: float                        # 0.5-1.5 multiplier
    avg_recovery_days: float                      # average days to full recovery

    # Training
    training_load_tolerance: float                # weekly load threshold (au)
    adaptation_rate: float                        # 0-1 (how fast user adapts)
    optimal_acwr: float                           # user's optimal ACWR (default 1.1)

    # Nutrition response
    carb_response: float                          # -1 to +1
    protein_response: float                       # -1 to +1
    sleep_recovery_factor: float                  # 0.5-1.5

    # Data quality
    confidence: float                             # 0-1 (data sufficiency)
    days_analyzed: int                            # days of history used
    data_sufficient: bool                         # True if enough data for reliable estimates
    insights: list[str]                           # personalized insights from learning

    def is_fast_metabolizer(self) -> bool:
        return self.metabolic_efficiency > 1.05

    def is_slow_metabolizer(self) -> bool:
        return self.metabolic_efficiency < 0.95

    def is_fast_recoverer(self) -> bool:
        return self.recovery_profile == "fast"

    def to_dict(self) -> dict:
        return {
            "true_tdee": round(self.true_tdee, 1) if self.true_tdee else None,
            "estimated_mifflin_tdee": round(self.estimated_mifflin_tdee, 1) if self.estimated_mifflin_tdee else None,
            "metabolic_efficiency": round(self.metabolic_efficiency, 3),
            "metabolic_trend": self.metabolic_trend,
            "recovery_profile": self.recovery_profile,
            "recovery_factor": round(self.recovery_factor, 2),
            "avg_recovery_days": round(self.avg_recovery_days, 1),
            "training_load_tolerance": round(self.training_load_tolerance, 1),
            "adaptation_rate": round(self.adaptation_rate, 3),
            "optimal_acwr": round(self.optimal_acwr, 2),
            "carb_response": round(self.carb_response, 3),
            "protein_response": round(self.protein_response, 3),
            "sleep_recovery_factor": round(self.sleep_recovery_factor, 2),
            "confidence": round(self.confidence, 3),
            "days_analyzed": self.days_analyzed,
            "data_sufficient": self.data_sufficient,
            "insights": self.insights,
        }


# --- Pure computation functions -----------------------------------------------

def _estimate_true_tdee(
    observations: list[WeightCalorieObservation],
) -> tuple[Optional[float], float]:
    """
    Estimate true TDEE from weight change + calorie history.

    Energy balance: calorie_deficit = weight_loss x 7700
    If weight stable -> true_tdee ~= mean(calories)
    If weight losing -> true_tdee = mean(calories) + (weight_loss_rate x 7700)
    If weight gaining -> true_tdee = mean(calories) - (weight_gain_rate x 7700)

    Returns: (true_tdee_kcal, confidence)
    """
    if len(observations) < MIN_DAYS_FOR_TDEE:
        return None, 0.0

    # Sort by date
    obs = sorted(observations, key=lambda x: x.obs_date)

    # Weight change over period
    weight_start = obs[0].weight_kg
    weight_end = obs[-1].weight_kg
    days = (obs[-1].obs_date - obs[0].obs_date).days

    if days < MIN_DAYS_FOR_TDEE:
        return None, 0.0

    # kg/day weight change (positive = gaining)
    weight_delta_per_day = (weight_end - weight_start) / days

    # Energy equivalent of weight change (kcal/day)
    # gaining weight -> surplus (TDEE < calories consumed)
    # losing weight -> deficit (TDEE > calories consumed)
    energy_delta_per_day = weight_delta_per_day * KCAL_PER_KG_FAT

    # Mean calorie consumption
    mean_calories = mean(o.calories_consumed for o in obs)

    # True TDEE
    true_tdee = mean_calories - energy_delta_per_day

    # Confidence based on data quantity and consistency
    calorie_consistency = 1.0
    if len(obs) >= 3:
        cal_std = stdev(o.calories_consumed for o in obs)
        calorie_consistency = max(0.3, 1.0 - (cal_std / max(mean_calories, 1)) * 0.5)

    confidence = min(1.0, len(obs) / 30) * calorie_consistency

    # Sanity check: TDEE should be between 1000 and 6000 kcal
    if not (1000 <= true_tdee <= 6000):
        logger.warning("Estimated TDEE %s out of reasonable range", round(true_tdee))
        true_tdee = max(1200, min(4500, true_tdee))
        confidence *= 0.5

    return true_tdee, confidence


def _compute_metabolic_efficiency(
    true_tdee: Optional[float],
    mifflin_tdee: Optional[float],
) -> tuple[float, str]:
    """
    Compute metabolic efficiency = true_tdee / mifflin_tdee.

    > 1.05 -> fast metabolizer (burns more than predicted)
    < 0.95 -> slow metabolizer (burns less than predicted)
    0.95-1.05 -> normal

    Returns: (efficiency, trend)
    """
    if not true_tdee or not mifflin_tdee or mifflin_tdee <= 0:
        return REFERENCE_EFFICIENCY, "stable"

    efficiency = true_tdee / mifflin_tdee
    efficiency = max(0.5, min(2.0, efficiency))  # clamp to reasonable range

    if efficiency > 1.05:
        trend = "improving"  # user burning more -> good adaptation
    elif efficiency < 0.95:
        trend = "declining"  # metabolic slowdown
    else:
        trend = "stable"

    return efficiency, trend


def _analyze_recovery_profile(
    readiness_obs: list[ReadinessObservation],
) -> tuple[str, float, float]:
    """
    Analyze recovery speed from readiness scores post hard training sessions.

    Returns: (profile, recovery_factor, avg_recovery_days)
    profile: "fast"|"normal"|"slow"
    recovery_factor: 0.5-1.5 (multiplier)
    avg_recovery_days: float
    """
    if len(readiness_obs) < 3:
        return "normal", 1.0, 1.5

    # Find days after hard training sessions and check recovery speed
    post_hard_readiness = []
    for i, obs in enumerate(readiness_obs):
        if obs.prior_training_load and obs.prior_training_load >= HARD_SESSION_THRESHOLD:
            post_hard_readiness.append(obs.readiness_score)

    if not post_hard_readiness:
        # No hard training sessions in history -- use overall readiness trend
        avg_readiness = mean(o.readiness_score for o in readiness_obs)
        if avg_readiness >= 75:
            return "fast", 1.2, 1.0
        elif avg_readiness >= 60:
            return "normal", 1.0, 1.5
        else:
            return "slow", 0.8, 2.0

    avg_post_hard = mean(post_hard_readiness)

    if avg_post_hard >= FAST_RECOVERY_THRESHOLD:
        profile = "fast"
        recovery_factor = 1.3
        avg_recovery_days = 1.0
    elif avg_post_hard >= NORMAL_RECOVERY_THRESHOLD:
        profile = "normal"
        recovery_factor = 1.0
        avg_recovery_days = 1.5
    else:
        profile = "slow"
        recovery_factor = 0.75
        avg_recovery_days = 2.5

    return profile, recovery_factor, avg_recovery_days


def _analyze_training_tolerance(
    training_obs: list[TrainingObservation],
) -> tuple[float, float, float]:
    """
    Analyze training load tolerance from history.

    Finds the maximum weekly load user sustains without:
    - ACWR going above 1.5 (overreaching)
    - Fatigue accumulating above 80

    Returns: (load_tolerance, adaptation_rate, optimal_acwr)
    """
    if len(training_obs) < MIN_SESSIONS_FOR_TOLERANCE:
        return 50.0, 0.5, 1.1  # conservative defaults

    loads = [o.training_load for o in training_obs]
    sustainable_loads = []

    for obs in training_obs:
        # Consider load sustainable if ACWR is in safe range and fatigue manageable
        acwr_ok = obs.acwr is None or obs.acwr <= 1.4
        fatigue_ok = obs.fatigue_score is None or obs.fatigue_score <= 75

        if acwr_ok and fatigue_ok:
            sustainable_loads.append(obs.training_load)

    if sustainable_loads:
        # Weekly tolerance = 7 x mean sustainable daily load
        daily_tolerance = mean(sustainable_loads)
        load_tolerance = daily_tolerance * 7
    else:
        load_tolerance = mean(loads) * 7 * 0.8  # conservative

    # Adaptation rate: how quickly user adapts (measured by tolerance growth over time)
    early_loads = loads[:len(loads)//2]
    late_loads = loads[len(loads)//2:]

    if early_loads and late_loads:
        early_mean = mean(early_loads)
        late_mean = mean(late_loads)
        if early_mean > 0:
            load_growth = (late_mean - early_mean) / early_mean
            adaptation_rate = max(0.0, min(1.0, 0.5 + load_growth))
        else:
            adaptation_rate = 0.5
    else:
        adaptation_rate = 0.5

    # Optimal ACWR from observations
    optimal_acwrs = [o.acwr for o in training_obs if o.acwr and 0.8 <= o.acwr <= 1.5]
    optimal_acwr = mean(optimal_acwrs) if optimal_acwrs else 1.1
    optimal_acwr = min(1.4, max(0.9, optimal_acwr))  # clamp

    return load_tolerance, adaptation_rate, optimal_acwr


def _analyze_nutrition_response(
    nutrition_obs: list[NutritionReadinessObservation],
    weight_kg: Optional[float] = None,
) -> tuple[float, float]:
    """
    Analyze carb and protein response from nutrition + performance data.

    Carb response: correlation between carb intake and next-day readiness
    Protein response: correlation between protein intake and readiness/body comp

    Returns: (carb_response, protein_response) both in range -1 to +1
    """
    if len(nutrition_obs) < MIN_DAYS_FOR_CARB_RESPONSE:
        return 0.0, 0.0

    # Filter observations with next-day readiness data
    with_readiness = [o for o in nutrition_obs if o.next_day_readiness is not None]

    if len(with_readiness) < 5:
        return 0.0, 0.0

    # Compute mean carb and protein intake
    mean_carbs = mean(o.carbs_g for o in with_readiness)
    mean_protein = mean(o.protein_g for o in with_readiness)
    mean_readiness = mean(o.next_day_readiness for o in with_readiness)

    # Simple correlation: high-carb days -> higher readiness?
    high_carb_readiness = [
        o.next_day_readiness for o in with_readiness
        if o.carbs_g > mean_carbs
    ]
    low_carb_readiness = [
        o.next_day_readiness for o in with_readiness
        if o.carbs_g <= mean_carbs
    ]

    if high_carb_readiness and low_carb_readiness:
        carb_diff = mean(high_carb_readiness) - mean(low_carb_readiness)
        carb_response = max(-1.0, min(1.0, carb_diff / 30))  # normalize to -1..+1
    else:
        carb_response = 0.0

    # Protein response: high protein -> better readiness
    high_protein_readiness = [
        o.next_day_readiness for o in with_readiness
        if o.protein_g > mean_protein
    ]
    low_protein_readiness = [
        o.next_day_readiness for o in with_readiness
        if o.protein_g <= mean_protein
    ]

    if high_protein_readiness and low_protein_readiness:
        protein_diff = mean(high_protein_readiness) - mean(low_protein_readiness)
        protein_response = max(-1.0, min(1.0, protein_diff / 30))
    else:
        protein_response = 0.0

    return carb_response, protein_response


def _analyze_sleep_recovery(
    sleep_minutes: list[float],
    readiness_scores: list[float],
) -> float:
    """
    Analyze relationship between sleep duration and readiness.

    sleep_recovery_factor:
    - 1.5 -> great sleeper (even short sleep -> high readiness)
    - 1.0 -> normal
    - 0.5 -> poor sleeper (needs lots of sleep to recover)

    Returns: sleep_recovery_factor (0.5-1.5)
    """
    if len(sleep_minutes) < 5 or len(readiness_scores) < 5:
        return 1.0

    # Pair sleep -> readiness (sleep on day N predicts readiness on day N+1)
    paired = list(zip(sleep_minutes[:len(readiness_scores)], readiness_scores))

    # Reference: 480 min (8h) -> target readiness
    mean_sleep = mean(s for s, _ in paired)
    mean_readiness = mean(r for _, r in paired)

    if mean_sleep <= 0:
        return 1.0

    # Normalize readiness to what it would be if sleep = 8h (480 min).
    # High readiness despite less sleep → efficient sleeper (factor > 1.0).
    # Low readiness despite full sleep → poor sleeper (factor < 1.0).
    normalized_readiness = mean_readiness * (480.0 / max(mean_sleep, 1.0))

    # Reference: 480 min sleep + 75 readiness → factor 1.0
    factor = max(0.5, min(1.5, normalized_readiness / 75.0))
    return factor


def _generate_insights(result: "UserLearningResult") -> list[str]:
    """Generate personalized insights from learning results."""
    insights = []

    if result.is_slow_metabolizer():
        insights.append(
            f"Votre metabolisme est {round((1 - result.metabolic_efficiency) * 100)}% "
            f"plus lent que predit. Ajustez votre TDEE estime a {round(result.true_tdee or 0)} kcal/j."
        )
    elif result.is_fast_metabolizer():
        insights.append(
            f"Votre metabolisme est {round((result.metabolic_efficiency - 1) * 100)}% "
            f"plus rapide que predit -- capacite d'adaptation elevee."
        )

    if result.recovery_profile == "fast":
        insights.append(
            "Recuperation rapide : vous pouvez enchainer les seances difficiles avec 24h de repos."
        )
    elif result.recovery_profile == "slow":
        insights.append(
            f"Recuperation lente ({result.avg_recovery_days:.1f}j en moyenne) : "
            f"prevoyez au moins 48h entre les seances intenses."
        )

    if result.carb_response > 0.3:
        insights.append(
            "Bonne reponse aux glucides : vos performances s'ameliorent significativement "
            "les jours de charge glucidique elevee."
        )
    elif result.carb_response < -0.3:
        insights.append(
            "Sensibilite glucidique : reduire les glucides ameliore vos marqueurs de recuperation."
        )

    if result.sleep_recovery_factor < 0.8:
        insights.append(
            "Qualite de sommeil a ameliorer : votre recuperation necessite davantage de sommeil "
            "que la moyenne pour atteindre un bon niveau de readiness."
        )
    elif result.sleep_recovery_factor > 1.2:
        insights.append(
            "Excellent dormeur : votre qualite de sommeil optimise votre recuperation."
        )

    if result.training_load_tolerance > 400:
        insights.append(
            f"Tolerance a l'entrainement elevee ({round(result.training_load_tolerance)} UA/semaine). "
            f"Progressez progressivement en maintenant un ACWR optimal de {result.optimal_acwr:.2f}."
        )

    return insights[:5]  # max 5 insights


def compute_user_learning_profile(
    weight_calorie_obs: list[WeightCalorieObservation] | None = None,
    readiness_obs: list[ReadinessObservation] | None = None,
    training_obs: list[TrainingObservation] | None = None,
    nutrition_readiness_obs: list[NutritionReadinessObservation] | None = None,
    sleep_minutes: list[float] | None = None,
    readiness_scores: list[float] | None = None,
    mifflin_tdee: Optional[float] = None,
) -> UserLearningResult:
    """
    Main entry point: compute personalized learning profile from all available history.

    All inputs are optional -- graceful degradation with missing data.
    Minimum data requirements:
    - TDEE: 14+ days weight + calories
    - Recovery: 3+ readiness observations
    - Training: 10+ training sessions
    - Nutrition: 7+ paired nutrition/readiness observations
    - Sleep: 5+ paired sleep/readiness observations
    """
    weight_calorie_obs = weight_calorie_obs or []
    readiness_obs = readiness_obs or []
    training_obs = training_obs or []
    nutrition_readiness_obs = nutrition_readiness_obs or []
    sleep_minutes = sleep_minutes or []
    readiness_scores = readiness_scores or []

    days_analyzed = max(
        len(weight_calorie_obs),
        len(readiness_obs),
        len(training_obs),
        len(nutrition_readiness_obs),
    )

    # -- TDEE estimation -------------------------------------------------------
    true_tdee, tdee_confidence = _estimate_true_tdee(weight_calorie_obs)
    metabolic_efficiency, metabolic_trend = _compute_metabolic_efficiency(
        true_tdee, mifflin_tdee
    )

    # -- Recovery profile ------------------------------------------------------
    recovery_profile, recovery_factor, avg_recovery_days = _analyze_recovery_profile(
        readiness_obs
    )

    # -- Training tolerance ----------------------------------------------------
    load_tolerance, adaptation_rate, optimal_acwr = _analyze_training_tolerance(
        training_obs
    )

    # -- Nutrition response ----------------------------------------------------
    carb_response, protein_response = _analyze_nutrition_response(
        nutrition_readiness_obs
    )

    # -- Sleep recovery --------------------------------------------------------
    sleep_recovery_factor = _analyze_sleep_recovery(sleep_minutes, readiness_scores)

    # -- Confidence (overall) --------------------------------------------------
    confidence_factors = []
    if weight_calorie_obs:
        confidence_factors.append(min(1.0, len(weight_calorie_obs) / 30))
    if readiness_obs:
        confidence_factors.append(min(1.0, len(readiness_obs) / 20))
    if training_obs:
        confidence_factors.append(min(1.0, len(training_obs) / 20))

    confidence = mean(confidence_factors) if confidence_factors else 0.0
    data_sufficient = confidence >= 0.5 and days_analyzed >= 14

    # -- Build result (pre-insights) -------------------------------------------
    result = UserLearningResult(
        true_tdee=true_tdee,
        estimated_mifflin_tdee=mifflin_tdee,
        metabolic_efficiency=metabolic_efficiency,
        metabolic_trend=metabolic_trend,
        recovery_profile=recovery_profile,
        recovery_factor=recovery_factor,
        avg_recovery_days=avg_recovery_days,
        training_load_tolerance=load_tolerance,
        adaptation_rate=adaptation_rate,
        optimal_acwr=optimal_acwr,
        carb_response=carb_response,
        protein_response=protein_response,
        sleep_recovery_factor=sleep_recovery_factor,
        confidence=confidence,
        days_analyzed=days_analyzed,
        data_sufficient=data_sufficient,
        insights=[],
    )

    # -- Generate insights -----------------------------------------------------
    result.insights = _generate_insights(result)

    return result


def build_learning_summary(result: UserLearningResult) -> str:
    """Compact summary (<=200 chars) for coach context."""
    tdee_str = f"TDEE reel {round(result.true_tdee or 0)} kcal" if result.true_tdee else "TDEE estime"
    return (
        f"Profil appris: {tdee_str}, efficacite {result.metabolic_efficiency:.2f}x, "
        f"recuperation {result.recovery_profile}, tolerance charge {round(result.training_load_tolerance)} AU/sem"
    )[:200]

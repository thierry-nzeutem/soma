from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

CRITICAL_ACWR = 1.8
HIGH_ACWR = 1.5
MODERATE_ACWR = 1.3
CRITICAL_ASYMMETRY = 60.0
HIGH_ASYMMETRY = 40.0
MODERATE_ASYMMETRY = 25.0
CRITICAL_FATIGUE = 85.0
HIGH_FATIGUE = 70.0
POOR_SLEEP = 300.0
VERY_POOR_SLEEP = 240.0
WEIGHT_ACWR = 0.30
WEIGHT_FATIGUE = 0.25
WEIGHT_ASYMMETRY = 0.20
WEIGHT_SLEEP = 0.15
WEIGHT_MONOTONY = 0.10


@dataclass
class RiskZone:
    """Identified risk zone in the body."""
    body_part: str
    risk_level: str
    risk_score: float
    contributing_factors: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "body_part": self.body_part,
            "risk_level": self.risk_level,
            "risk_score": round(self.risk_score, 1),
            "contributing_factors": self.contributing_factors,
            "recommendations": self.recommendations,
        }


@dataclass
class InjuryPreventionResult:
    """Complete injury prevention analysis."""
    analysis_date: date
    injury_risk_score: float
    injury_risk_category: str
    acwr_risk_score: float
    fatigue_risk_score: float
    asymmetry_risk_score: float
    sleep_risk_score: float
    monotony_risk_score: float
    risk_zones: list[RiskZone]
    movement_compensation_patterns: list[str]
    fatigue_compensation_risk: bool
    training_overload_risk: bool
    recommendations: list[str]
    immediate_actions: list[str]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "injury_risk_score": round(self.injury_risk_score, 1),
            "injury_risk_category": self.injury_risk_category,
            "acwr_risk_score": round(self.acwr_risk_score, 1),
            "fatigue_risk_score": round(self.fatigue_risk_score, 1),
            "asymmetry_risk_score": round(self.asymmetry_risk_score, 1),
            "sleep_risk_score": round(self.sleep_risk_score, 1),
            "monotony_risk_score": round(self.monotony_risk_score, 1),
            "risk_zones": [z.to_dict() for z in self.risk_zones],
            "movement_compensation_patterns": self.movement_compensation_patterns,
            "fatigue_compensation_risk": self.fatigue_compensation_risk,
            "training_overload_risk": self.training_overload_risk,
            "recommendations": self.recommendations,
            "immediate_actions": self.immediate_actions,
            "confidence": round(self.confidence, 3),
        }


def _score_acwr_risk(acwr: Optional[float]) -> float:
    """Score ACWR risk. Zones: <0.8 undertrain, 0.8-1.3 optimal, >1.3 rising risk, >1.8 critical."""
    if acwr is None:
        return 20.0
    if acwr < 0.5:
        return 30.0
    elif acwr < 0.8:
        return 15.0
    elif acwr <= 1.3:
        return 0.0 + (acwr - 0.8) / 0.5 * 10
    elif acwr <= 1.5:
        return min(50.0, 10 + (acwr - 1.3) / 0.2 * 40)
    elif acwr <= 1.8:
        return min(85.0, 50 + (acwr - 1.5) / 0.3 * 35)
    else:
        return 85.0 + min(15.0, (acwr - 1.8) * 30)


def _score_fatigue_risk(fatigue_score: Optional[float]) -> float:
    """Score fatigue risk. High fatigue alters biomechanics."""
    if fatigue_score is None:
        return 15.0
    if fatigue_score < 30:
        return 0.0
    elif fatigue_score < 50:
        return (fatigue_score - 30) / 20 * 15
    elif fatigue_score < 70:
        return 15 + (fatigue_score - 50) / 20 * 35
    elif fatigue_score < 85:
        return 50 + (fatigue_score - 70) / 15 * 35
    else:
        return min(100.0, 85 + (fatigue_score - 85) / 15 * 15)


def _score_asymmetry_risk(asymmetry_score: Optional[float]) -> float:
    """Score movement asymmetry risk. High asymmetry overloads one side."""
    if asymmetry_score is None:
        return 10.0
    if asymmetry_score < 15:
        return 0.0
    elif asymmetry_score < MODERATE_ASYMMETRY:
        return (asymmetry_score - 15) / 10 * 20
    elif asymmetry_score < HIGH_ASYMMETRY:
        return 20 + (asymmetry_score - MODERATE_ASYMMETRY) / 15 * 40
    elif asymmetry_score < CRITICAL_ASYMMETRY:
        return 60 + (asymmetry_score - HIGH_ASYMMETRY) / 20 * 30
    else:
        return min(100.0, 90 + (asymmetry_score - CRITICAL_ASYMMETRY) * 0.5)


def _score_sleep_risk(sleep_minutes: Optional[float]) -> float:
    """Score sleep deprivation risk. Poor sleep reduces form quality."""
    if sleep_minutes is None:
        return 10.0
    if sleep_minutes >= 480:
        return 0.0
    elif sleep_minutes >= 420:
        return 10.0
    elif sleep_minutes >= 360:
        return 25.0
    elif sleep_minutes >= 300:
        return 55.0
    elif sleep_minutes >= 240:
        return 80.0
    else:
        return 100.0


def _score_monotony_risk(training_loads: list[float]) -> float:
    """Score training monotony (Foster 1998). Monotony = mean/std."""
    if len(training_loads) < 3:
        return 0.0
    from statistics import mean, stdev
    m = mean(training_loads)
    if m == 0:
        return 0.0
    try:
        s = stdev(training_loads)
    except Exception:
        s = 1.0
    monotony = m / max(s, 1.0)
    # Foster 1998: monotony > 2.0 is associated with increased injury risk.
    # Threshold widened to 2.5 to correctly classify highly-varied loads as low risk.
    if monotony < 2.0:
        return 0.0
    elif monotony < 2.5:
        return 20.0
    elif monotony < 3.5:
        return 50.0
    elif monotony < 5.0:
        return 75.0
    else:
        return 100.0


def _determine_risk_category(score: float) -> str:
    """Map 0-100 score to risk category string."""
    if score < 15:
        return "minimal"
    elif score < 30:
        return "low"
    elif score < 55:
        return "moderate"
    elif score < 75:
        return "high"
    else:
        return "critical"


def _identify_risk_zones(
    asymmetry_score: Optional[float],
    exercise_profiles: Optional[dict],
    fatigue_score: Optional[float],
    acwr: Optional[float],
) -> list[RiskZone]:
    """Identify body parts at risk based on motion analysis and training patterns."""
    zones: list[RiskZone] = []

    # Lower back risk
    lb_risk = 0.0
    lb_factors: list[str] = []
    if fatigue_score and fatigue_score > 70:
        lb_risk += 30
        lb_factors.append("fatigue_élevée")
    if acwr and acwr > 1.3:
        lb_risk += 20
        lb_factors.append("charge_soudaine")
    if asymmetry_score and asymmetry_score > 30:
        lb_risk += 25
        lb_factors.append("asymétrie_mouvement")
    if lb_risk > 20:
        zones.append(RiskZone(
            body_part="lower_back",
            risk_level=_determine_risk_category(lb_risk),
            risk_score=lb_risk,
            contributing_factors=lb_factors,
            recommendations=[
                "Renforcer les muscles stabilisateurs du core",
                "Réduire la charge si fatigue > 70",
            ],
        ))

    # Knee risk
    knee_risk = 0.0
    knee_factors: list[str] = []
    if exercise_profiles:
        for ex_key in ("squat", "lunge"):
            profile = exercise_profiles.get(ex_key, {})
            if profile and profile.get("quality_trend") == "declining":
                knee_risk += 30
                knee_factors.append("qualité_" + profile.get("exercise_type", ex_key) + "_en_baisse")
    if acwr and acwr > 1.4:
        knee_risk += 25
        knee_factors.append("surcharge_progressive")
    if knee_risk > 20:
        zones.append(RiskZone(
            body_part="knee",
            risk_level=_determine_risk_category(knee_risk),
            risk_score=knee_risk,
            contributing_factors=knee_factors,
            recommendations=[
                "Corriger la technique de squat/fente",
                "Renforcer les ischio-jambiers",
            ],
        ))

    # Shoulder risk
    shoulder_risk = 0.0
    shoulder_factors: list[str] = []
    if exercise_profiles:
        pushup_profile = exercise_profiles.get("push_up", {})
        if pushup_profile:
            if pushup_profile.get("quality_trend") == "declining":
                shoulder_risk += 40
                shoulder_factors.append("qualité_pompes_en_baisse")
            if pushup_profile.get("avg_stability", 80) < 60:
                shoulder_risk += 25
                shoulder_factors.append("stabilité_épaule_insuffisante")
    if shoulder_risk > 20:
        zones.append(RiskZone(
            body_part="shoulder",
            risk_level=_determine_risk_category(shoulder_risk),
            risk_score=shoulder_risk,
            contributing_factors=shoulder_factors,
            recommendations=[
                "Renforcer la coiffe des rotateurs",
                "Améliorer la stabilité d’épaule",
            ],
        ))

    return zones


def _detect_compensation_patterns(
    asymmetry_score: Optional[float],
    exercise_profiles: Optional[dict],
    fatigue_score: Optional[float],
) -> list[str]:
    """Detect movement compensation patterns."""
    patterns: list[str] = []
    if asymmetry_score and asymmetry_score > MODERATE_ASYMMETRY:
        patterns.append("asymétrie_latérale_détectée")
    if fatigue_score and fatigue_score > HIGH_FATIGUE:
        patterns.append("compensation_par_fatigue_musculaire")
    if exercise_profiles:
        for ex, profile in exercise_profiles.items():
            if profile.get("avg_stability", 80) < 60 and profile.get("avg_amplitude", 80) > 80:
                patterns.append("compensation_mobilité_par_instabilité_" + ex)
    return patterns


def _generate_recommendations(
    result: "InjuryPreventionResult",
) -> tuple[list[str], list[str]]:
    """Generate recommendations and immediate actions."""
    recommendations: list[str] = []
    immediate_actions: list[str] = []
    category = result.injury_risk_category

    if result.training_overload_risk:
        if category in ("critical", "high"):
            immediate_actions.append(
                "⚠️ RÉDUIRE la charge d’entraînement de 30-40% cette semaine — risque élevé de blessure."
            )
        else:
            recommendations.append(
                "Réduire l’ACWR en dessous de 1.3 en limitant l’augmentation de charge à max +10%/semaine."
            )

    if result.fatigue_compensation_risk:
        if category in ("critical", "high"):
            immediate_actions.append(
                "⚠️ REPOS obligatoire 1-2 jours — fatigue critique altérant la biomécanique."
            )
        else:
            recommendations.append(
                "Intégrer une séance de récupération active (mobilité, stretching) avant la prochaine séance intense."
            )

    for zone in result.risk_zones:
        if zone.risk_level in ("high", "critical"):
            for rec in zone.recommendations:
                if rec not in immediate_actions:
                    immediate_actions.append("[" + zone.body_part + "] " + rec)

    if result.asymmetry_risk_score > 50:
        recommendations.append(
            "Corriger l’asymétrie de mouvement : travailler côté par côté avec exercices unilatéraux."
        )

    if result.sleep_risk_score > 40:
        recommendations.append(
            "Améliorer la qualité du sommeil : objectif 7-8h pour réduire le risque de blessure."
        )

    if result.monotony_risk_score > 50:
        recommendations.append(
            "Varier l’intensité des séances : alterner intensité élevée/modérée/faible pour réduire la monotonie."
        )

    if not recommendations and not immediate_actions:
        recommendations.append(
            "Risque minimal — continuez votre programme actuel avec progression prudente."
        )

    return recommendations[:5], immediate_actions[:3]


def compute_injury_prevention_analysis(
    acwr: Optional[float] = None,
    fatigue_score: Optional[float] = None,
    asymmetry_score: Optional[float] = None,
    sleep_minutes_avg: Optional[float] = None,
    training_loads_7d: Optional[list[float]] = None,
    exercise_profiles: Optional[dict] = None,
    readiness_score: Optional[float] = None,
    target_date: Optional[date] = None,
) -> InjuryPreventionResult:
    """Main entry point: compute comprehensive injury prevention analysis."""
    target_date = target_date or date.today()
    training_loads = training_loads_7d or []

    acwr_risk = _score_acwr_risk(acwr)
    fatigue_risk = _score_fatigue_risk(fatigue_score)
    asymmetry_risk = _score_asymmetry_risk(asymmetry_score)
    sleep_risk = _score_sleep_risk(sleep_minutes_avg)
    monotony_risk = _score_monotony_risk(training_loads)

    injury_risk_score = (
        WEIGHT_ACWR * acwr_risk
        + WEIGHT_FATIGUE * fatigue_risk
        + WEIGHT_ASYMMETRY * asymmetry_risk
        + WEIGHT_SLEEP * sleep_risk
        + WEIGHT_MONOTONY * monotony_risk
    )
    injury_risk_score = round(min(100.0, max(0.0, injury_risk_score)), 1)

    training_overload_risk = (acwr is not None and acwr > MODERATE_ACWR)
    fatigue_compensation_risk = (fatigue_score is not None and fatigue_score > HIGH_FATIGUE)

    risk_zones = _identify_risk_zones(
        asymmetry_score=asymmetry_score,
        exercise_profiles=exercise_profiles,
        fatigue_score=fatigue_score,
        acwr=acwr,
    )

    compensation_patterns = _detect_compensation_patterns(
        asymmetry_score=asymmetry_score,
        exercise_profiles=exercise_profiles,
        fatigue_score=fatigue_score,
    )

    data_points = sum([
        acwr is not None,
        fatigue_score is not None,
        asymmetry_score is not None,
        sleep_minutes_avg is not None,
        bool(training_loads),
        bool(exercise_profiles),
    ])
    confidence = min(1.0, data_points / 6)

    result = InjuryPreventionResult(
        analysis_date=target_date,
        injury_risk_score=injury_risk_score,
        injury_risk_category=_determine_risk_category(injury_risk_score),
        acwr_risk_score=acwr_risk,
        fatigue_risk_score=fatigue_risk,
        asymmetry_risk_score=asymmetry_risk,
        sleep_risk_score=sleep_risk,
        monotony_risk_score=monotony_risk,
        risk_zones=risk_zones,
        movement_compensation_patterns=compensation_patterns,
        fatigue_compensation_risk=fatigue_compensation_risk,
        training_overload_risk=training_overload_risk,
        recommendations=[],
        immediate_actions=[],
        confidence=confidence,
    )

    recommendations, immediate_actions = _generate_recommendations(result)
    result.recommendations = recommendations
    result.immediate_actions = immediate_actions
    return result


def build_injury_summary(result: InjuryPreventionResult) -> str:
    """Compact summary (<=200 chars) for coach context."""
    zones_str = ", ".join(z.body_part for z in result.risk_zones[:2]) if result.risk_zones else "aucune zone"
    summary = (
        "Risque blessure " + str(round(result.injury_risk_score)) + "/100 (" + result.injury_risk_category + "), "
        "zones: " + zones_str + ". ACWR: " + str(round(result.acwr_risk_score)) + "/100, "
        "fatigue: " + str(round(result.fatigue_risk_score)) + "/100"
    )
    return summary[:200]

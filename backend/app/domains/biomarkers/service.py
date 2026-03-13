"""
SOMA LOT 16 — Longevity Lab Biomarkers Engine.

Analyzes lab results to compute:
- metabolic_health_score: 0-100
- inflammation_score: 0-100 (higher = worse)
- cardiovascular_risk: 0-100
- longevity_modifier: -10 to +10 years (adjusts BiologicalAge)

Supported biomarkers (10+):
vitamin_d, ferritin, crp (C-reactive protein), testosterone,
hba1c, fasting_glucose, cholesterol_total, hdl, ldl, triglycerides,
cortisol, homocysteine, magnesium, zinc, omega3_index
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Reference ranges (WHO / clinical standards) ──────────────────────────────────────────────

REFERENCE_RANGES: dict[str, dict] = {
    "vitamin_d": {
        "unit": "ng/mL",
        "optimal_low": 40, "optimal_high": 70,
        "adequate_low": 20, "adequate_high": 100,
        "deficient_below": 20, "toxic_above": 150,
        "category": "micronutrient",
    },
    "ferritin": {
        "unit": "ng/mL",
        "optimal_low": 30, "optimal_high": 150,
        "adequate_low": 12, "adequate_high": 300,
        "deficient_below": 12, "toxic_above": 400,
        "category": "iron_status",
    },
    "crp": {
        "unit": "mg/L",
        "optimal_low": 0, "optimal_high": 0.8,
        "adequate_low": 0, "adequate_high": 3.0,
        "deficient_below": None, "toxic_above": 10.0,
        "category": "inflammation",
        "lower_is_better": True,
    },
    "testosterone_total": {
        "unit": "ng/dL",
        "optimal_low": 500, "optimal_high": 900,
        "adequate_low": 300, "adequate_high": 1100,
        "deficient_below": 300, "toxic_above": 1100,
        "category": "hormonal",
    },
    "hba1c": {
        "unit": "%",
        "optimal_low": 4.5, "optimal_high": 5.4,
        "adequate_low": 4.0, "adequate_high": 5.9,
        "deficient_below": None, "toxic_above": 6.5,
        "category": "metabolic",
        "lower_is_better": True,
    },
    "fasting_glucose": {
        "unit": "mg/dL",
        "optimal_low": 75, "optimal_high": 90,
        "adequate_low": 70, "adequate_high": 100,
        "deficient_below": 70, "toxic_above": 126,
        "category": "metabolic",
        "lower_is_better": True,
    },
    "cholesterol_total": {
        "unit": "mg/dL",
        "optimal_low": 150, "optimal_high": 180,
        "adequate_low": 130, "adequate_high": 200,
        "deficient_below": 130, "toxic_above": 240,
        "category": "cardiovascular",
        "lower_is_better": True,
    },
    "hdl": {
        "unit": "mg/dL",
        "optimal_low": 60, "optimal_high": 90,
        "adequate_low": 40, "adequate_high": 100,
        "deficient_below": 40, "toxic_above": None,
        "category": "cardiovascular",
    },
    "ldl": {
        "unit": "mg/dL",
        "optimal_low": 0, "optimal_high": 100,
        "adequate_low": 0, "adequate_high": 130,
        "deficient_below": None, "toxic_above": 160,
        "category": "cardiovascular",
        "lower_is_better": True,
    },
    "triglycerides": {
        "unit": "mg/dL",
        "optimal_low": 0, "optimal_high": 100,
        "adequate_low": 0, "adequate_high": 150,
        "deficient_below": None, "toxic_above": 200,
        "category": "cardiovascular",
        "lower_is_better": True,
    },
    "cortisol": {
        "unit": "mcg/dL",
        "optimal_low": 6, "optimal_high": 18,
        "adequate_low": 4, "adequate_high": 22,
        "deficient_below": 4, "toxic_above": 25,
        "category": "stress",
    },
    "homocysteine": {
        "unit": "mcmol/L",
        "optimal_low": 0, "optimal_high": 9,
        "adequate_low": 0, "adequate_high": 12,
        "deficient_below": None, "toxic_above": 15,
        "category": "cardiovascular",
        "lower_is_better": True,
    },
    "magnesium": {
        "unit": "mg/dL",
        "optimal_low": 2.0, "optimal_high": 2.6,
        "adequate_low": 1.7, "adequate_high": 2.9,
        "deficient_below": 1.7, "toxic_above": 3.0,
        "category": "micronutrient",
    },
    "omega3_index": {
        "unit": "%",
        "optimal_low": 8, "optimal_high": 12,
        "adequate_low": 4, "adequate_high": 12,
        "deficient_below": 4, "toxic_above": None,
        "category": "cardiovascular",
    },
}

# Category weights for composite scores
METABOLIC_MARKERS = ["hba1c", "fasting_glucose", "triglycerides"]
INFLAMMATION_MARKERS = ["crp", "homocysteine", "ferritin"]
CARDIOVASCULAR_MARKERS = ["cholesterol_total", "hdl", "ldl", "triglycerides", "homocysteine"]
LONGEVITY_MARKERS = ["vitamin_d", "omega3_index", "magnesium", "hba1c", "crp", "testosterone_total"]


# ─── Data structures ──────────────────────────────────────────────────────────────────────────────────

@dataclass
class BiomarkerResult:
    """Single lab result for a biomarker."""
    marker_name: str
    value: float
    unit: str
    lab_date: date
    source: str = "manual"        # "manual"|"lab_import"|"device"
    confidence: float = 1.0       # 0-1

    def to_dict(self) -> dict:
        return {
            "marker_name": self.marker_name,
            "value": self.value,
            "unit": self.unit,
            "lab_date": self.lab_date.isoformat(),
            "source": self.source,
            "confidence": self.confidence,
        }


@dataclass
class BiomarkerAnalysis:
    """Analysis of a single biomarker against reference ranges."""
    marker_name: str
    value: float
    unit: str
    status: str              # "optimal"|"adequate"|"suboptimal"|"deficient"|"elevated"|"toxic"
    score: float             # 0-100 (100 = optimal health)
    deviation_pct: float     # % from optimal center
    interpretation: str
    recommendations: list[str]

    def to_dict(self) -> dict:
        return {
            "marker_name": self.marker_name,
            "value": self.value,
            "unit": self.unit,
            "status": self.status,
            "score": round(self.score, 1),
            "deviation_pct": round(self.deviation_pct, 1),
            "interpretation": self.interpretation,
            "recommendations": self.recommendations,
        }


@dataclass
class BiomarkerAnalysisResult:
    """Complete biomarker analysis."""
    analysis_date: date

    # Composite scores
    metabolic_health_score: float        # 0-100
    inflammation_score: float            # 0-100 (higher = worse)
    cardiovascular_risk: float           # 0-100
    longevity_modifier: float            # -10 to +10 years

    # Individual analyses
    marker_analyses: list[BiomarkerAnalysis]

    # Summary
    markers_analyzed: int
    optimal_markers: int
    suboptimal_markers: int
    deficient_markers: list[str]
    elevated_markers: list[str]

    # Recommendations
    priority_actions: list[str]
    supplementation_recommendations: list[str]
    dietary_recommendations: list[str]

    # Confidence
    confidence: float                    # based on recency + marker count

    def to_dict(self) -> dict:
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "metabolic_health_score": round(self.metabolic_health_score, 1),
            "inflammation_score": round(self.inflammation_score, 1),
            "cardiovascular_risk": round(self.cardiovascular_risk, 1),
            "longevity_modifier": round(self.longevity_modifier, 2),
            "marker_analyses": [m.to_dict() for m in self.marker_analyses],
            "markers_analyzed": self.markers_analyzed,
            "optimal_markers": self.optimal_markers,
            "suboptimal_markers": self.suboptimal_markers,
            "deficient_markers": self.deficient_markers,
            "elevated_markers": self.elevated_markers,
            "priority_actions": self.priority_actions,
            "supplementation_recommendations": self.supplementation_recommendations,
            "dietary_recommendations": self.dietary_recommendations,
            "confidence": round(self.confidence, 3),
        }


# ─── Pure analysis functions ───────────────────────────────────────────────────────────────────────────

def _analyze_single_marker(
    marker_name: str,
    value: float,
) -> BiomarkerAnalysis:
    """Analyze a single biomarker against its reference range."""
    ref = REFERENCE_RANGES.get(marker_name)
    if not ref:
        return BiomarkerAnalysis(
            marker_name=marker_name,
            value=value,
            unit="unknown",
            status="unknown",
            score=50.0,
            deviation_pct=0.0,
            interpretation="Marqueur non reconnu dans la base de référence.",
            recommendations=[],
        )

    unit = ref["unit"]
    opt_low = ref["optimal_low"]
    opt_high = ref["optimal_high"]
    adeq_low = ref.get("adequate_low")
    adeq_high = ref.get("adequate_high")
    deficient_below = ref.get("deficient_below")
    toxic_above = ref.get("toxic_above")

    # Determine status
    if toxic_above is not None and value > toxic_above:
        status = "toxic"
        score = 0.0
    elif deficient_below is not None and value < deficient_below:
        status = "deficient"
        score = 10.0
    elif opt_low is not None and opt_high is not None and opt_low <= value <= opt_high:
        status = "optimal"
        score = 100.0
    elif adeq_low is not None and adeq_high is not None and adeq_low <= value <= adeq_high:
        status = "adequate"
        # Score between 60-90 based on proximity to optimal
        opt_center = (opt_low + opt_high) / 2
        dist_from_optimal = abs(value - opt_center)
        adeq_range = max(adeq_high - adeq_low, 1)
        score = 90 - (dist_from_optimal / adeq_range * 30)
        score = max(60.0, min(90.0, score))
    else:
        status = "suboptimal"
        score = 35.0

    # Deviation from optimal center
    opt_center = (opt_low + opt_high) / 2 if (opt_low is not None and opt_high is not None) else value
    deviation_pct = ((value - opt_center) / max(opt_center, 1)) * 100

    # Interpretation and recommendations
    interp, recs = _get_interpretation(marker_name, status, value, ref)

    return BiomarkerAnalysis(
        marker_name=marker_name,
        value=value,
        unit=unit,
        status=status,
        score=score,
        deviation_pct=deviation_pct,
        interpretation=interp,
        recommendations=recs,
    )


def _get_interpretation(
    marker_name: str,
    status: str,
    value: float,
    ref: dict,
) -> tuple[str, list[str]]:
    """Generate interpretation text and recommendations for a biomarker."""
    interps: dict[str, dict[str, tuple[str, list[str]]]] = {
        "vitamin_d": {
            "deficient": (
                "Carence en vitamine D — risque osseux, immunitaire et de fatigue chronique.",
                ["Supplémenter 4000-6000 UI/j sous contrôle médical", "Exposition solaire quotidienne 15-20min"],
            ),
            "optimal": ("Vitamine D optimale — bon soutien immunitaire et osseux.", []),
            "adequate": ("Vitamine D correcte mais non optimale.", ["Supplémenter 2000 UI/j pour atteindre l'optimum"]),
            "suboptimal": ("Vitamine D insuffisante.", ["Supplémenter 3000-4000 UI/j sous contrôle médical"]),
        },
        "crp": {
            "optimal": ("CRP optimale — inflammation systémique minimale.", []),
            "adequate": (
                "CRP légèrement élevée — inflammation de bas grade.",
                ["Augmenter omega-3, antioxydants", "Optimiser le sommeil"],
            ),
            "suboptimal": (
                "CRP élevée — inflammation chronique.",
                ["Bilan anti-inflammatoire", "Éliminer les aliments pro-inflammatoires"],
            ),
            "toxic": ("CRP très élevée — inflammation aiguë ou chronique sévère.", ["Consulter un médecin en urgence"]),
        },
        "hba1c": {
            "optimal": ("HbA1c optimale — excellent contrôle glycémique.", []),
            "adequate": ("HbA1c normale.", []),
            "suboptimal": (
                "HbA1c limite — prédiabète possible.",
                ["Réduire sucres raffinés", "Augmenter activité physique"],
            ),
            "toxic": ("HbA1c diabétique — consultation médicale urgente.", ["Consulter un médecin"]),
        },
        "hdl": {
            "deficient": (
                "HDL trop bas — risque cardiovasculaire augmenté.",
                ["Augmenter activité physique", "Consommer acides gras mono-insaturés"],
            ),
            "optimal": ("HDL excellent — bon cardioprotecteur.", []),
            "adequate": ("HDL correct.", []),
        },
        "ldl": {
            "optimal": ("LDL optimal.", []),
            "adequate": ("LDL légèrement élevé.", ["Réduire graisses saturées"]),
            "suboptimal": (
                "LDL élevé — risque cardiovasculaire.",
                ["Alimentation méditerranéenne", "Activité physique régulière"],
            ),
            "toxic": ("LDL très élevé — consultation médicale.", ["Consulter un médecin"]),
        },
    }

    default_interp: dict[str, tuple[str, list[str]]] = {
        "optimal": (f"{marker_name} dans la plage optimale.", []),
        "adequate": (f"{marker_name} correct mais non optimal.", []),
        "suboptimal": (
            f"{marker_name} hors plage — amélioration possible.",
            [f"Optimiser {marker_name} par l'alimentation et le mode de vie"],
        ),
        "deficient": (
            f"Carence en {marker_name}.",
            [f"Supplémenter ou optimiser l'apport en {marker_name}"],
        ),
        "elevated": (f"{marker_name} élevé.", [f"Réduire {marker_name} par l'alimentation"]),
        "toxic": (
            f"{marker_name} à niveau toxique — consultation médicale urgente.",
            ["Consulter un médecin"],
        ),
    }

    marker_interps = interps.get(marker_name, {})
    interp_data = marker_interps.get(status, default_interp.get(status, (f"{marker_name}: {status}", [])))
    return interp_data[0], interp_data[1]


def _compute_metabolic_health_score(
    analyses: list[BiomarkerAnalysis],
) -> float:
    """Composite metabolic health score from metabolic markers."""
    metabolic = [
        a for a in analyses
        if REFERENCE_RANGES.get(a.marker_name, {}).get("category") == "metabolic"
    ]
    if not metabolic:
        return 70.0  # default if no metabolic markers
    return sum(a.score for a in metabolic) / len(metabolic)


def _compute_inflammation_score(
    analyses: list[BiomarkerAnalysis],
) -> float:
    """Inflammation score (0-100, higher = worse) from inflammation markers."""
    inflam = [a for a in analyses if a.marker_name in INFLAMMATION_MARKERS]
    if not inflam:
        return 20.0  # default low inflammation
    avg_score = sum(a.score for a in inflam) / len(inflam)
    return max(0.0, 100.0 - avg_score)  # invert: high marker score = low inflammation


def _compute_cardiovascular_risk(
    analyses: list[BiomarkerAnalysis],
) -> float:
    """Cardiovascular risk score (0-100) from cardiovascular markers."""
    cardio = [a for a in analyses if a.marker_name in CARDIOVASCULAR_MARKERS]
    if not cardio:
        return 20.0
    avg_score = sum(a.score for a in cardio) / len(cardio)
    return max(0.0, 100.0 - avg_score)  # invert (lower marker score = higher risk)


def _compute_longevity_modifier(
    analyses: list[BiomarkerAnalysis],
    metabolic_health_score: float,
    inflammation_score: float,
    cardiovascular_risk: float,
) -> float:
    """
    Compute longevity age modifier: -10 to +10 years.

    Negative = biomarkers indicate biological age YOUNGER than chronological.
    Positive = biomarkers indicate biological age OLDER.

    Formula: modifier = (75 - longevity_score) * 0.2
    """
    longevity_markers_analyses = [a for a in analyses if a.marker_name in LONGEVITY_MARKERS]

    if longevity_markers_analyses:
        longevity_score = sum(a.score for a in longevity_markers_analyses) / len(longevity_markers_analyses)
    else:
        longevity_score = (metabolic_health_score + (100 - inflammation_score) + (100 - cardiovascular_risk)) / 3

    # modifier: excellent health (score=90) -> -3 years; poor health (score=40) -> +7 years
    modifier = (75 - longevity_score) * 0.2
    return max(-10.0, min(10.0, modifier))


def _generate_priority_actions(
    analyses: list[BiomarkerAnalysis],
    inflammation_score: float,
    cardiovascular_risk: float,
) -> tuple[list[str], list[str], list[str]]:
    """Generate priority, supplementation, and dietary recommendations."""
    priority: list[str] = []
    supplements: list[str] = []
    dietary: list[str] = []

    # Check critical markers
    for analysis in analyses:
        if analysis.status in ("toxic", "deficient"):
            if analysis.status == "toxic":
                priority.append(f"{analysis.marker_name.upper()} critique — consultation médicale urgente")
            else:
                priority.append(f"Corriger la carence en {analysis.marker_name}")
            for rec in analysis.recommendations[:1]:
                if "supplément" in rec.lower() or "ui" in rec.lower():
                    supplements.append(rec)
                else:
                    priority.append(rec)

    # Inflammation
    if inflammation_score > 60:
        dietary.append("Adopter une alimentation anti-inflammatoire (méditerranéenne, riche en omega-3)")
        supplements.append("Omega-3 EPA+DHA 2-3g/j pour réduire l'inflammation")

    # Cardiovascular
    if cardiovascular_risk > 50:
        dietary.append("Réduire les graisses saturées, augmenter les fibres et les phytostérols")
        priority.append("Bilan cardiovasculaire complet recommandé")

    # Suboptimal longevity markers needing supplementation
    suboptimal_sups = [
        f"Optimiser {a.marker_name}"
        for a in analyses
        if a.status == "suboptimal" and a.marker_name in ("vitamin_d", "magnesium", "omega3_index")
    ]
    supplements.extend(suboptimal_sups[:2])

    return priority[:4], supplements[:4], dietary[:3]


def compute_biomarker_analysis(
    biomarker_results: list[BiomarkerResult],
) -> BiomarkerAnalysisResult:
    """
    Main entry point: analyze a list of lab results.

    Returns comprehensive BiomarkerAnalysisResult.
    """
    if not biomarker_results:
        return BiomarkerAnalysisResult(
            analysis_date=date.today(),
            metabolic_health_score=70.0,
            inflammation_score=20.0,
            cardiovascular_risk=25.0,
            longevity_modifier=0.0,
            marker_analyses=[],
            markers_analyzed=0,
            optimal_markers=0,
            suboptimal_markers=0,
            deficient_markers=[],
            elevated_markers=[],
            priority_actions=["Effectuer un bilan biologique complet pour personnaliser votre analyse."],
            supplementation_recommendations=[],
            dietary_recommendations=[],
            confidence=0.0,
        )

    # Analyze each recognized marker
    analyses = [
        _analyze_single_marker(r.marker_name, r.value)
        for r in biomarker_results
        if r.marker_name in REFERENCE_RANGES
    ]

    # Compute composite scores
    metabolic_health = _compute_metabolic_health_score(analyses)
    inflammation = _compute_inflammation_score(analyses)
    cardiovascular = _compute_cardiovascular_risk(analyses)
    longevity_mod = _compute_longevity_modifier(analyses, metabolic_health, inflammation, cardiovascular)

    # Categorize markers
    optimal = [a for a in analyses if a.status == "optimal"]
    suboptimal = [a for a in analyses if a.status in ("suboptimal", "adequate")]
    deficient = [a.marker_name for a in analyses if a.status == "deficient"]
    elevated = [a.marker_name for a in analyses if a.status in ("elevated", "toxic")]

    # Recommendations
    priority, supplements, dietary = _generate_priority_actions(analyses, inflammation, cardiovascular)

    # Confidence (based on marker count)
    confidence = min(1.0, len(analyses) / 10)

    return BiomarkerAnalysisResult(
        analysis_date=date.today(),
        metabolic_health_score=metabolic_health,
        inflammation_score=inflammation,
        cardiovascular_risk=cardiovascular,
        longevity_modifier=longevity_mod,
        marker_analyses=analyses,
        markers_analyzed=len(analyses),
        optimal_markers=len(optimal),
        suboptimal_markers=len(suboptimal),
        deficient_markers=deficient,
        elevated_markers=elevated,
        priority_actions=priority,
        supplementation_recommendations=supplements,
        dietary_recommendations=dietary,
        confidence=confidence,
    )


def build_biomarker_summary(result: BiomarkerAnalysisResult) -> str:
    """Compact summary (≤200 chars) for coach context."""
    return (
        f"Biomarqueurs ({result.markers_analyzed} analysés): "
        f"métabolique {result.metabolic_health_score:.0f}/100, "
        f"inflammation {result.inflammation_score:.0f}/100, "
        f"cardio-risque {result.cardiovascular_risk:.0f}/100, "
        f"modifier âge bio: {result.longevity_modifier:+.1f}ans"
    )[:200]

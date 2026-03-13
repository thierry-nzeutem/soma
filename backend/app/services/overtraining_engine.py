"""
Overtraining Engine SOMA — LOT 10.

Évalue le risque de surentraînement en combinant le ratio charge aiguë/chronique (ACWR),
le bien-être subjectif (sommeil + fatigue) et le score de récupération global.

L'ACWR est le prédicteur le plus robuste scientifiquement validé.
Score final : moyenne pondérée des composantes disponibles (0-100).

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional
from dataclasses import dataclass, field


# ── Poids des composantes ──────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "acwr":      0.40,   # Indicateur biomécanique le plus fiable
    "wellbeing": 0.35,   # Sommeil + fatigue (bien-être subjectif)
    "readiness": 0.25,   # Score de récupération global
}

# Seuils de niveau de risque (partagés avec injury_risk_engine)
_RISK_LEVELS = [
    (25.0,  "low"),
    (50.0,  "moderate"),
    (75.0,  "high"),
    (100.1, "critical"),
]

# Zones ACWR → étiquettes scientifiques
_ACWR_ZONES: list[tuple[float, str]] = [
    (0.8,  "undertraining"),
    (1.3,  "optimal"),
    (1.5,  "moderate_risk"),
    (2.0,  "high_risk"),
    (9999, "overreaching"),
]


# ── Dataclass résultat ─────────────────────────────────────────────────────────

@dataclass
class OvertrainingResult:
    """Résultat complet du calcul du risque de surentraînement."""
    overtraining_risk: float = 0.0             # 0–100
    risk_level: str = "low"                    # low / moderate / high / critical
    acwr: Optional[float] = None               # valeur ACWR calculée
    acwr_zone: str = "unknown"                 # zone ACWR textuelle
    recommendation: str = ""                   # conseil principal (1 phrase)
    components: dict = field(default_factory=dict)
    confidence: float = 0.0                    # 0–1 (somme des poids disponibles)


# ── Fonctions pures ────────────────────────────────────────────────────────────

def _compute_acwr(training_load_7d: float, training_load_28d: float) -> Optional[float]:
    """
    ACWR = charge_aiguë_7j / (charge_chronique_28j / 4).
    Normalise la charge chronique en équivalent hebdomadaire.
    Retourne None si la charge chronique est nulle (évite division par zéro).
    """
    chronic_weekly = training_load_28d / 4.0
    if chronic_weekly <= 0:
        return None
    return round(training_load_7d / chronic_weekly, 3)


def _acwr_zone(acwr: float) -> str:
    """
    Classifie un ACWR dans une zone de risque textuellement.
    Basé sur les études Foster (2001) et Hulin (2016).
    """
    for threshold, zone in _ACWR_ZONES:
        if acwr < threshold:
            return zone
    return "overreaching"


def _score_acwr_overtraining(acwr: float) -> float:
    """
    Score de risque ACWR pour le surentraînement (0–100).
    Zone optimale 0.8–1.3 → faible risque.
    Undertraining (<0.8) : déconditionnement → risque faible mais réel.
    >2.0 : surcharge aiguë majeure → risque critique.
    """
    if acwr <= 0:
        return 0.0
    if acwr < 0.8:
        # Undertraining : faible risque de surentraînement
        return round(max(0.0, (0.8 - acwr) / 0.8 * 15.0), 1)
    if acwr <= 1.3:
        # Zone optimale
        return round(5.0 + (acwr - 0.8) / 0.5 * 5.0, 1)    # 5→10
    if acwr <= 1.5:
        return round(10.0 + (acwr - 1.3) / 0.2 * 30.0, 1)  # 10→40
    if acwr <= 2.0:
        return round(40.0 + (acwr - 1.5) / 0.5 * 40.0, 1)  # 40→80
    return round(min(100.0, 80.0 + (acwr - 2.0) * 15.0), 1)


def _score_wellbeing(
    sleep_score: Optional[float],
    fatigue_score: Optional[float],
) -> Optional[float]:
    """
    Score de bien-être subjectif (0–100) combinant sommeil et fatigue.
    Mauvais sommeil + fatigue élevée = indicateur fort de surentraînement.
    Retourne None si les deux données sont absentes.
    """
    sub_scores: list[float] = []

    if sleep_score is not None:
        # Sommeil faible = risque élevé (inversé)
        if sleep_score >= 80:
            sleep_risk = 10.0
        elif sleep_score >= 60:
            sleep_risk = 10.0 + (80.0 - sleep_score) * 1.2  # 10→34
        elif sleep_score >= 40:
            sleep_risk = 34.0 + (60.0 - sleep_score) * 1.8  # 34→70
        else:
            sleep_risk = min(100.0, 70.0 + (40.0 - sleep_score) * 1.5)
        sub_scores.append(round(sleep_risk, 1))

    if fatigue_score is not None:
        # Fatigue élevée = risque élevé (direct)
        if fatigue_score <= 30:
            fatigue_risk = fatigue_score * 0.25           # 0→7.5
        elif fatigue_score <= 60:
            fatigue_risk = 7.5 + (fatigue_score - 30) * 1.0  # 7.5→37.5
        elif fatigue_score <= 80:
            fatigue_risk = 37.5 + (fatigue_score - 60) * 1.75  # 37.5→72.5
        else:
            fatigue_risk = min(100.0, 72.5 + (fatigue_score - 80) * 1.4)
        sub_scores.append(round(fatigue_risk, 1))

    if not sub_scores:
        return None
    return round(sum(sub_scores) / len(sub_scores), 1)


def _score_readiness_overtraining(readiness_score: float) -> float:
    """
    Score de risque basé sur la readiness (0–100).
    Readiness faible = corps non récupéré = indicateur de surentraînement.
    """
    if readiness_score >= 80:
        return 8.0
    if readiness_score >= 60:
        return round(8.0 + (80.0 - readiness_score) * 1.0, 1)   # 8→28
    if readiness_score >= 40:
        return round(28.0 + (60.0 - readiness_score) * 1.8, 1)  # 28→64
    return round(min(100.0, 64.0 + (40.0 - readiness_score) * 1.8), 1)


def _risk_level(score: float) -> str:
    """Convertit un score 0–100 en niveau de risque textuel."""
    for threshold, level in _RISK_LEVELS:
        if score < threshold:
            return level
    return "critical"


def _build_recommendation(
    risk_level: str,
    acwr_zone: str,
    acwr: Optional[float],
) -> str:
    """Génère une recommandation principale selon la zone ACWR et le niveau de risque."""
    if risk_level == "low":
        if acwr_zone == "undertraining":
            return "Ta charge d'entraînement est faible — augmente progressivement (max +10 %/semaine)."
        return "Ton ratio charge/récupération est optimal. Continue ton programme actuel."

    if acwr_zone == "overreaching" or (acwr is not None and acwr >= 2.0):
        return (
            "⚠ Surcharge aiguë majeure détectée (ACWR ≥ 2.0). "
            "Repos obligatoire 48–72h, puis reprise progressive."
        )
    if acwr_zone == "high_risk" or risk_level == "high":
        return (
            "Charge d'entraînement trop élevée par rapport à ta base chronique. "
            "Réduis l'intensité de 25–30 % cette semaine."
        )
    if acwr_zone == "moderate_risk":
        return (
            "Charge hebdomadaire légèrement élevée. "
            "Intègre une séance de récupération active et surveille ta fatigue."
        )
    if risk_level == "moderate":
        return (
            "Signes modérés de fatigue accumulée. "
            "Assure-toi de dormir 8h et d'hydratation correcte."
        )
    return "Surveille ta charge et ta récupération pour prévenir le surentraînement."


# ── Fonction principale ────────────────────────────────────────────────────────

def compute_overtraining_risk(
    training_load_7d: Optional[float] = None,
    training_load_28d: Optional[float] = None,
    sleep_score: Optional[float] = None,
    fatigue_score: Optional[float] = None,
    readiness_score: Optional[float] = None,
) -> OvertrainingResult:
    """
    Calcule le risque de surentraînement multi-factoriel.

    Paramètres
    ----------
    training_load_7d : charge aiguë (7 derniers jours)
    training_load_28d : charge chronique (28 derniers jours)
    sleep_score : score de qualité de sommeil 0–100
    fatigue_score : score de fatigue 0–100 (MetabolicTwin)
    readiness_score : score de récupération 0–100

    Retourne
    --------
    OvertrainingResult avec score global, zone ACWR, recommandation et confidence.
    """
    components: dict[str, float] = {}
    total_weight = 0.0
    weighted_sum = 0.0

    # ── Composante ACWR ────────────────────────────────────────────────────────
    acwr_value: Optional[float] = None
    zone = "unknown"

    if training_load_7d is not None and training_load_28d is not None:
        acwr_value = _compute_acwr(training_load_7d, training_load_28d)
        if acwr_value is not None:
            zone = _acwr_zone(acwr_value)
            s = _score_acwr_overtraining(acwr_value)
            components["acwr"] = round(s, 1)
            weighted_sum += s * _WEIGHTS["acwr"]
            total_weight += _WEIGHTS["acwr"]

    # ── Composante Bien-être ───────────────────────────────────────────────────
    wellbeing_score = _score_wellbeing(sleep_score, fatigue_score)
    if wellbeing_score is not None:
        components["wellbeing"] = round(wellbeing_score, 1)
        weighted_sum += wellbeing_score * _WEIGHTS["wellbeing"]
        total_weight += _WEIGHTS["wellbeing"]

    # ── Composante Readiness ──────────────────────────────────────────────────
    if readiness_score is not None:
        s = _score_readiness_overtraining(readiness_score)
        components["readiness"] = round(s, 1)
        weighted_sum += s * _WEIGHTS["readiness"]
        total_weight += _WEIGHTS["readiness"]

    # ── Agrégation ────────────────────────────────────────────────────────────
    if total_weight == 0.0:
        return OvertrainingResult(
            overtraining_risk=0.0,
            risk_level="low",
            acwr=acwr_value,
            acwr_zone="unknown",
            recommendation="Données insuffisantes pour évaluer le risque de surentraînement.",
            components=components,
            confidence=0.0,
        )

    overtraining_risk = round(weighted_sum / total_weight, 1)
    confidence = round(total_weight, 2)
    level = _risk_level(overtraining_risk)
    recommendation = _build_recommendation(level, zone, acwr_value)

    return OvertrainingResult(
        overtraining_risk=overtraining_risk,
        risk_level=level,
        acwr=acwr_value,
        acwr_zone=zone,
        recommendation=recommendation,
        components=components,
        confidence=confidence,
    )

"""
Injury Risk Engine SOMA — LOT 10.

Calcule le risque de blessure en fonction de la charge d'entraînement (ACWR),
de la fatigue, de la qualité biomécanique (proxy vision) et de la récupération.

Score final : moyenne pondérée des composantes disponibles (0-100).
Niveau de risque : low / moderate / high / critical.

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional
from dataclasses import dataclass, field


# ── Poids des composantes ──────────────────────────────────────────────────────

_WEIGHTS: dict[str, float] = {
    "acwr":         0.35,   # Acute/Chronic Workload Ratio — principal prédicteur
    "fatigue":      0.25,   # Score de fatigue (MetabolicTwin)
    "biomechanics": 0.25,   # Qualité de mouvement (VisionSessions)
    "readiness":    0.15,   # Score de récupération global
}

# Seuils de niveau de risque
_RISK_LEVELS = [
    (25.0,  "low"),
    (50.0,  "moderate"),
    (75.0,  "high"),
    (100.1, "critical"),
]

# Étiquettes lisibles par composante
_COMPONENT_LABELS: dict[str, str] = {
    "acwr":         "training_load",
    "fatigue":      "fatigue",
    "biomechanics": "biomechanics",
    "readiness":    "recovery",
}


# ── Dataclass résultat ─────────────────────────────────────────────────────────

@dataclass
class InjuryRiskResult:
    """Résultat complet du calcul du risque de blessure."""
    injury_risk_score: float = 0.0              # 0–100
    risk_level: str = "low"                     # low / moderate / high / critical
    risk_area: str = "unknown"                  # composante dominante
    primary_risk_factor: str = "insufficient_data"
    acwr: Optional[float] = None                # valeur ACWR calculée
    components: dict = field(default_factory=dict)    # scores bruts par composante
    recommendations: list = field(default_factory=list)
    confidence: float = 0.0                     # 0–1 (somme des poids disponibles)


# ── Fonctions de scoring pures ─────────────────────────────────────────────────

def _compute_acwr(training_load_7d: float, training_load_28d: float) -> Optional[float]:
    """
    ACWR = charge_7j / (charge_28j / 4).
    Normalise la charge chronique (28j) en charge hebdomadaire avant division.
    Retourne None si la charge chronique est nulle.
    """
    chronic_weekly = training_load_28d / 4.0
    if chronic_weekly <= 0:
        return None
    return round(training_load_7d / chronic_weekly, 3)


def _score_acwr_risk(acwr: float) -> float:
    """
    Risque ACWR (0–100).
    Zone sûre 0.8–1.3 → faible risque (~10).
    Undertraining (<0.8) → risque faible.
    1.3–1.5 → risque modéré (10→45).
    1.5–2.0 → risque élevé (45→80).
    >2.0 → risque critique (>80).
    """
    if acwr <= 0:
        return 0.0
    if acwr < 0.8:
        # Undertraining : risque faible mais non nul (déconditionnement)
        return round(max(0.0, 20.0 - acwr * 20.0), 1)
    if acwr <= 1.3:
        # Zone sûre
        return 10.0
    if acwr <= 1.5:
        # Risque modéré croissant
        return round(10.0 + (acwr - 1.3) / 0.2 * 35.0, 1)
    if acwr <= 2.0:
        # Risque élevé
        return round(45.0 + (acwr - 1.5) / 0.5 * 35.0, 1)
    # Risque critique
    return round(min(100.0, 80.0 + (acwr - 2.0) * 20.0), 1)


def _score_fatigue_risk(fatigue_score: float) -> float:
    """
    Risque lié à la fatigue (0–100).
    fatigue_score 0–100 provient du MetabolicTwin.
    Fatigue élevée → muscles, tendons et ligaments moins résistants → risque blessure.
    ≤40 : faible, 40–70 : modéré, 70–85 : élevé, >85 : critique.
    """
    if fatigue_score <= 0:
        return 0.0
    if fatigue_score <= 40:
        return round(fatigue_score * 0.3, 1)    # 0→12
    if fatigue_score <= 70:
        return round(12.0 + (fatigue_score - 40) * 1.2, 1)  # 12→48
    if fatigue_score <= 85:
        return round(48.0 + (fatigue_score - 70) * 2.0, 1)  # 48→78
    return round(min(100.0, 78.0 + (fatigue_score - 85) * 1.5), 1)  # 78→100


def _score_biomechanics_risk(avg_quality_score: float) -> float:
    """
    Risque biomécanique (0–100).
    avg_quality_score = moyenne(stability_score, amplitude_score) des VisionSessions récentes.
    Faible qualité de mouvement → schémas moteurs défectueux → risque de blessure accru.
    Score inversé : qualité élevée = faible risque.
    ≥80 : faible, 60–80 : modéré bas, 40–60 : modéré haut, <40 : élevé.
    """
    if avg_quality_score >= 80:
        return 10.0
    if avg_quality_score >= 60:
        return round(10.0 + (80.0 - avg_quality_score) * 1.0, 1)    # 10→30
    if avg_quality_score >= 40:
        return round(30.0 + (60.0 - avg_quality_score) * 2.0, 1)    # 30→70
    return round(min(100.0, 70.0 + (40.0 - avg_quality_score) * 1.5), 1)  # 70→100


def _score_readiness_risk(readiness_score: float) -> float:
    """
    Risque lié à la récupération insuffisante (0–100).
    readiness 0–100 : faible readiness = récupération incomplète = risque élevé.
    ≥75 : faible, 50–75 : modéré, 30–50 : élevé, <30 : critique.
    """
    if readiness_score >= 75:
        return 10.0
    if readiness_score >= 50:
        return round(10.0 + (75.0 - readiness_score) * 1.2, 1)   # 10→40
    if readiness_score >= 30:
        return round(40.0 + (50.0 - readiness_score) * 2.0, 1)   # 40→80
    return round(min(100.0, 80.0 + (30.0 - readiness_score) * 1.0), 1)  # 80→110→100


def _risk_level(score: float) -> str:
    """Convertit un score 0–100 en niveau de risque textuel."""
    for threshold, level in _RISK_LEVELS:
        if score < threshold:
            return level
    return "critical"


def _risk_area(component_scores: dict[str, float]) -> tuple[str, str]:
    """
    Retourne (risk_area, primary_risk_factor) :
    la composante avec le score brut le plus élevé est la zone primaire.
    """
    if not component_scores:
        return "unknown", "insufficient_data"

    top_key = max(component_scores, key=lambda k: component_scores[k])
    area = _COMPONENT_LABELS.get(top_key, top_key)

    # Si plusieurs composantes sont proches (±10), zone "combined"
    top_score = component_scores[top_key]
    high_count = sum(1 for s in component_scores.values() if s >= top_score - 10 and s >= 30)
    if high_count >= 2 and top_score >= 40:
        return "combined", "multiple_risk_factors"

    return area, f"high_{top_key}_risk"


def _build_recommendations(risk_level: str, risk_area: str, acwr: Optional[float]) -> list[str]:
    """Génère des recommandations contextualisées selon le risque."""
    recs = []

    if risk_level == "low":
        recs.append("Continue ton programme d'entraînement actuel, ton risque de blessure est faible.")
        return recs

    if risk_area in ("training_load", "combined") or (acwr is not None and acwr > 1.5):
        recs.append("Réduis la charge d'entraînement de 20–30 % cette semaine pour respecter la règle des 10 %.")

    if risk_area == "fatigue":
        recs.append("Intègre une journée de récupération active (marche, étirements) avant ta prochaine séance intense.")

    if risk_area == "biomechanics":
        recs.append("Concentre-toi sur la qualité d'exécution plutôt que la charge — un coach ou une séance CV peut aider.")

    if risk_area == "recovery":
        recs.append("Priorise le sommeil (8h) et l'hydratation pour améliorer ta récupération.")

    if risk_level in ("high", "critical"):
        recs.append("Consulte un professionnel de santé si tu ressens une gêne ou douleur persistante.")
        if risk_level == "critical":
            recs.insert(0, "⚠ Risque élevé : envisage un repos complet de 48–72h avant de reprendre.")

    if not recs:
        recs.append("Surveille ta charge hebdomadaire et assure-toi de dormir suffisamment.")

    return recs


# ── Fonction principale ────────────────────────────────────────────────────────

def compute_injury_risk(
    training_load_7d: Optional[float] = None,
    training_load_28d: Optional[float] = None,
    fatigue_score: Optional[float] = None,
    avg_vision_quality: Optional[float] = None,  # proxy biomécanique VisionSessions
    readiness_score: Optional[float] = None,
) -> InjuryRiskResult:
    """
    Calcule le risque de blessure multi-factoriel.

    Paramètres
    ----------
    training_load_7d : charge aiguë (7 derniers jours)
    training_load_28d : charge chronique (28 derniers jours)
    fatigue_score : score de fatigue 0–100 (MetabolicTwin)
    avg_vision_quality : moyenne stability+amplitude des VisionSessions (7j) — proxy asymétrie
    readiness_score : score de récupération 0–100

    Retourne
    --------
    InjuryRiskResult avec score global, niveau, zone primaire, confidence et recommandations.
    """
    component_scores: dict[str, float] = {}
    total_weight = 0.0
    weighted_sum = 0.0

    # ── Composante ACWR ────────────────────────────────────────────────────────
    acwr_value: Optional[float] = None
    if training_load_7d is not None and training_load_28d is not None:
        acwr_value = _compute_acwr(training_load_7d, training_load_28d)
        if acwr_value is not None:
            s = _score_acwr_risk(acwr_value)
            component_scores["acwr"] = round(s, 1)
            weighted_sum += s * _WEIGHTS["acwr"]
            total_weight += _WEIGHTS["acwr"]

    # ── Composante Fatigue ────────────────────────────────────────────────────
    if fatigue_score is not None:
        s = _score_fatigue_risk(fatigue_score)
        component_scores["fatigue"] = round(s, 1)
        weighted_sum += s * _WEIGHTS["fatigue"]
        total_weight += _WEIGHTS["fatigue"]

    # ── Composante Biomécanique ───────────────────────────────────────────────
    if avg_vision_quality is not None:
        s = _score_biomechanics_risk(avg_vision_quality)
        component_scores["biomechanics"] = round(s, 1)
        weighted_sum += s * _WEIGHTS["biomechanics"]
        total_weight += _WEIGHTS["biomechanics"]

    # ── Composante Readiness ──────────────────────────────────────────────────
    if readiness_score is not None:
        s = _score_readiness_risk(readiness_score)
        component_scores["readiness"] = round(s, 1)
        weighted_sum += s * _WEIGHTS["readiness"]
        total_weight += _WEIGHTS["readiness"]

    # ── Agrégation ────────────────────────────────────────────────────────────
    if total_weight == 0.0:
        return InjuryRiskResult(
            injury_risk_score=0.0,
            risk_level="low",
            risk_area="unknown",
            primary_risk_factor="insufficient_data",
            acwr=acwr_value,
            components=component_scores,
            recommendations=["Données insuffisantes pour évaluer le risque de blessure."],
            confidence=0.0,
        )

    # Score normalisé (ramène au poids réellement disponible)
    injury_risk_score = round(weighted_sum / total_weight, 1)
    confidence = round(total_weight, 2)

    level = _risk_level(injury_risk_score)
    area, primary = _risk_area(component_scores)
    recs = _build_recommendations(level, area, acwr_value)

    return InjuryRiskResult(
        injury_risk_score=injury_risk_score,
        risk_level=level,
        risk_area=area,
        primary_risk_factor=primary,
        acwr=acwr_value,
        components=component_scores,
        recommendations=recs,
        confidence=confidence,
    )

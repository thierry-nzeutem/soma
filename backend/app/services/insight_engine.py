"""
Insight Engine SOMA — LOT 3.

Analyse les DailyMetrics des 7 derniers jours pour détecter des patterns
santé préoccupants. Chaque insight correspond à une règle précise et
transparente.

Règles de détection :
  1. Protéines insuffisantes (< 60% cible, 3j+ sur 7)
  2. Déficit calorique excessif (< 60% cible, 2j+ sur 5 avec données)
  3. Manque d'activité (pas < 50% objectif, 5j+ sur 7)
  4. Fatigue cumulée (readiness < 50, 3j+ sur 5 avec données)
  5. Dette de sommeil (< 6h, 3j+ sur 7)
  6. Déshydratation chronique (hydratation < 60%, 4j+ sur 7)
  7. Risque de surentraînement (charge 7j > 1.5× charge 28j)

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

# ── Constantes seuils ──────────────────────────────────────────────────────────

MIN_SLEEP_HOURS = 6.0                # h — seuil "nuit courte"
STEPS_DAILY_GOAL = 8_000             # pas par jour
PROTEIN_RATIO_MIN = 0.60             # 60% de la cible = seuil d'alerte
CALORIE_RATIO_MIN = 0.60             # 60% de la cible = déficit excessif
HYDRATION_RATIO_MIN = 0.60           # 60% de la cible = déshydratation
READINESS_LOW = 50.0                 # Score readiness bas

PROTEIN_ALERT_DAYS = 3               # jours consécutifs / sur 7
CALORIE_ALERT_DAYS = 2               # sur 5 jours avec données
ACTIVITY_ALERT_DAYS = 5              # sur 7
FATIGUE_ALERT_DAYS = 3               # sur 5 avec données
SLEEP_ALERT_DAYS = 3                 # sur 7
HYDRATION_ALERT_DAYS = 4             # sur 7

OVERTRAINING_RATIO = 1.5             # ACWR > 1.5 = zone rouge


# ── Dataclass insight détecté ──────────────────────────────────────────────────

@dataclass
class DetectedInsight:
    """Insight détecté par le moteur d'analyse."""
    category: str        # nutrition | sleep | activity | recovery | training | hydration | weight
    severity: str        # info | warning | critical
    title: str
    message: str
    action: Optional[str] = None
    data_evidence: Dict[str, Any] = field(default_factory=dict)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _count_days_below_ratio(
    values: list,
    targets: list,
    ratio: float,
) -> int:
    """Compte les jours où value / target < ratio (jours avec target défini)."""
    count = 0
    for v, t in zip(values, targets):
        if t and t > 0 and v is not None:
            if (v / t) < ratio:
                count += 1
    return count


def _count_days_below_abs(values: list, threshold: float) -> int:
    """Compte les jours où value < threshold (valeur absolue)."""
    return sum(1 for v in values if v is not None and v < threshold)


def _days_with_data(values: list) -> int:
    """Compte les jours avec données disponibles."""
    return sum(1 for v in values if v is not None)


def _safe_ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


# ── Règles de détection ────────────────────────────────────────────────────────

def detect_low_protein(metrics_7d: list) -> Optional[DetectedInsight]:
    """
    Détecte un apport protéique insuffisant sur 7 jours.
    Seuil : protein < 60% de protein_target_g pendant >= 3 jours.
    """
    proteins = [getattr(m, "protein_g", None) for m in metrics_7d]
    targets = [getattr(m, "protein_target_g", None) for m in metrics_7d]

    days_low = _count_days_below_ratio(proteins, targets, PROTEIN_RATIO_MIN)
    days_data = _days_with_data(proteins)

    if days_data < 2 or days_low < PROTEIN_ALERT_DAYS:
        return None

    avg_protein = sum(p for p in proteins if p) / max(1, days_data)
    avg_target = sum(t for t in targets if t) / max(1, _days_with_data(targets))

    return DetectedInsight(
        category="nutrition",
        severity="warning",
        title="Apport protéique insuffisant",
        message=f"Apport protéique inférieur à {int(PROTEIN_RATIO_MIN*100)}% de la cible "
                f"pendant {days_low} jours sur les 7 derniers ({avg_protein:.0f}g vs {avg_target:.0f}g cible).",
        action="Augmenter les sources de protéines : viande maigre, poisson, œufs, légumineuses, produits laitiers.",
        data_evidence={
            "days_below_threshold": days_low,
            "avg_protein_g": round(avg_protein, 1),
            "avg_target_g": round(avg_target, 1),
            "threshold_pct": int(PROTEIN_RATIO_MIN * 100),
        },
    )


def detect_excessive_calorie_deficit(metrics_7d: list) -> Optional[DetectedInsight]:
    """
    Détecte un déficit calorique excessif.
    Seuil : calories < 60% de la cible pendant >= 2 jours (sur jours avec données).
    """
    cals = [getattr(m, "calories_consumed", None) for m in metrics_7d]
    targets = [getattr(m, "calories_target", None) for m in metrics_7d]

    days_data = _days_with_data(cals)
    if days_data < 2:
        return None

    days_low = _count_days_below_ratio(cals, targets, CALORIE_RATIO_MIN)
    if days_low < CALORIE_ALERT_DAYS:
        return None

    avg_cal = sum(c for c in cals if c) / max(1, days_data)

    return DetectedInsight(
        category="nutrition",
        severity="critical",
        title="Déficit calorique excessif",
        message=f"Apport calorique inférieur à {int(CALORIE_RATIO_MIN*100)}% de la cible "
                f"pendant {days_low} jours ({avg_cal:.0f} kcal/j en moyenne). "
                "Un déficit excessif ralentit le métabolisme et dégrade la masse musculaire.",
        action="Augmenter progressivement l'apport calorique. Viser un déficit de 300-500 kcal max.",
        data_evidence={
            "days_below_threshold": days_low,
            "avg_calories_kcal": round(avg_cal, 0),
            "threshold_pct": int(CALORIE_RATIO_MIN * 100),
        },
    )


def detect_low_activity(metrics_7d: list) -> Optional[DetectedInsight]:
    """
    Détecte un manque d'activité physique.
    Seuil : steps < 50% de l'objectif pendant >= 5 jours.
    """
    steps_list = [getattr(m, "steps", None) for m in metrics_7d]
    days_data = _days_with_data(steps_list)
    if days_data < 3:
        return None

    days_low = sum(
        1 for s in steps_list
        if s is not None and s < STEPS_DAILY_GOAL * 0.5
    )
    if days_low < ACTIVITY_ALERT_DAYS:
        return None

    avg_steps = sum(s for s in steps_list if s) / max(1, days_data)

    return DetectedInsight(
        category="activity",
        severity="warning",
        title="Sédentarité prolongée",
        message=f"Moins de {int(STEPS_DAILY_GOAL * 0.5):,} pas/j pendant {days_low} jours "
                f"(moyenne : {avg_steps:.0f} pas). "
                "La sédentarité prolongée augmente le risque cardiovasculaire et métabolique.",
        action=f"Viser {STEPS_DAILY_GOAL:,} pas/jour. Commencer par 15-20 min de marche quotidienne.",
        data_evidence={
            "days_below_threshold": days_low,
            "avg_steps": round(avg_steps, 0),
            "goal_steps": STEPS_DAILY_GOAL,
        },
    )


def detect_accumulated_fatigue(metrics_7d: list) -> Optional[DetectedInsight]:
    """
    Détecte une fatigue cumulée (readiness score bas).
    Seuil : readiness < 50 pendant >= 3 jours (sur jours avec données).
    """
    readiness = [getattr(m, "readiness_score", None) for m in metrics_7d]
    days_data = _days_with_data(readiness)
    if days_data < 2:
        return None

    days_low = _count_days_below_abs(readiness, READINESS_LOW)
    if days_low < FATIGUE_ALERT_DAYS:
        return None

    avg_readiness = sum(r for r in readiness if r) / max(1, days_data)

    return DetectedInsight(
        category="recovery",
        severity="critical",
        title="Fatigue cumulée",
        message=f"Score de récupération inférieur à {int(READINESS_LOW)} pendant {days_low} jours "
                f"(moyenne : {avg_readiness:.1f}/100). "
                "La fatigue accumulée augmente le risque de blessure et de sur-entraînement.",
        action="Planifier 2-3 jours de récupération active. Prioriser sommeil, nutrition et mobilité.",
        data_evidence={
            "days_low_readiness": days_low,
            "avg_readiness": round(avg_readiness, 1),
            "threshold": int(READINESS_LOW),
        },
    )


def detect_sleep_debt(metrics_7d: list) -> Optional[DetectedInsight]:
    """
    Détecte une dette de sommeil chronique.
    Seuil : durée de sommeil < 6h pendant >= 3 nuits.
    """
    sleep_mins = [getattr(m, "sleep_minutes", None) for m in metrics_7d]
    days_data = _days_with_data(sleep_mins)
    if days_data < 3:
        return None

    threshold_mins = MIN_SLEEP_HOURS * 60
    days_short = _count_days_below_abs(sleep_mins, threshold_mins)
    if days_short < SLEEP_ALERT_DAYS:
        return None

    avg_sleep_h = sum(s / 60 for s in sleep_mins if s) / max(1, days_data)

    return DetectedInsight(
        category="sleep",
        severity="critical",
        title="Dette de sommeil chronique",
        message=f"Moins de {MIN_SLEEP_HOURS}h de sommeil pendant {days_short} nuits sur les 7 dernières "
                f"(moyenne : {avg_sleep_h:.1f}h). "
                "Le manque de sommeil chronique altère la récupération, les performances cognitives et la composition corporelle.",
        action="Avancer l'heure de coucher de 30-60 min. Éviter écrans et caféine après 18h. Viser 7-9h par nuit.",
        data_evidence={
            "nights_below_threshold": days_short,
            "avg_sleep_hours": round(avg_sleep_h, 1),
            "threshold_hours": MIN_SLEEP_HOURS,
        },
    )


def detect_dehydration_pattern(metrics_7d: list) -> Optional[DetectedInsight]:
    """
    Détecte une déshydratation chronique.
    Seuil : hydratation < 60% de la cible pendant >= 4 jours.
    """
    hydration = [getattr(m, "hydration_ml", None) for m in metrics_7d]
    targets = [getattr(m, "hydration_target_ml", None) for m in metrics_7d]

    days_data = _days_with_data(hydration)
    if days_data < 3:
        return None

    days_low = _count_days_below_ratio(hydration, targets, HYDRATION_RATIO_MIN)
    if days_low < HYDRATION_ALERT_DAYS:
        return None

    avg_hydration = sum(h for h in hydration if h) / max(1, days_data)

    return DetectedInsight(
        category="hydration",
        severity="warning",
        title="Déshydratation chronique",
        message=f"Apport hydrique inférieur à {int(HYDRATION_RATIO_MIN*100)}% de la cible "
                f"pendant {days_low} jours ({avg_hydration:.0f}ml/j en moyenne). "
                "La déshydratation chronique affecte les performances et la cognition.",
        action="Viser minimum 2L/j. Garder une gourde visible. Démarrer chaque repas avec un verre d'eau.",
        data_evidence={
            "days_below_threshold": days_low,
            "avg_hydration_ml": round(avg_hydration, 0),
            "threshold_pct": int(HYDRATION_RATIO_MIN * 100),
        },
    )


def detect_overtraining_risk(
    training_load_7d: Optional[float],
    training_load_28d: Optional[float],
) -> Optional[DetectedInsight]:
    """
    Détecte un risque de sur-entraînement via l'ACWR (Acute:Chronic Workload Ratio).
    Seuil : charge_7j / charge_28j > 1.5 (zone rouge).
    """
    if not training_load_7d or not training_load_28d or training_load_28d < 1:
        return None

    acwr = training_load_7d / training_load_28d
    if acwr <= OVERTRAINING_RATIO:
        return None

    severity = "critical" if acwr > 2.0 else "warning"

    return DetectedInsight(
        category="training",
        severity=severity,
        title="Risque de sur-entraînement",
        message=f"Ratio de charge aiguë/chronique (ACWR) = {acwr:.2f} "
                f"(charge 7j : {training_load_7d:.0f}, charge 28j : {training_load_28d:.0f}). "
                "Un ACWR > 1.5 indique un risque élevé de blessure.",
        action="Réduire le volume d'entraînement de 30-40% cette semaine. Prioriser mobilité et récupération active.",
        data_evidence={
            "acwr": round(acwr, 2),
            "training_load_7d": round(training_load_7d, 1),
            "training_load_28d": round(training_load_28d, 1),
            "threshold": OVERTRAINING_RATIO,
        },
    )


# ── Moteur principal ───────────────────────────────────────────────────────────

def run_insight_engine(
    metrics_7d: list,
    training_load_28d: Optional[float] = None,
) -> List[DetectedInsight]:
    """
    Exécute toutes les règles d'analyse sur les 7 derniers jours de métriques.

    Paramètres :
      - metrics_7d : liste de DailyMetrics (jusqu'à 7 objets)
      - training_load_28d : charge entraînement cumulée sur 28j (pour ACWR)

    Retourne la liste des insights détectés, triés par sévérité.
    """
    insights: List[DetectedInsight] = []

    if not metrics_7d:
        return insights

    # Charge 7j pour ACWR
    load_7d = sum(
        (getattr(m, "training_load", None) or 0)
        for m in metrics_7d
    )

    rules = [
        lambda: detect_low_protein(metrics_7d),
        lambda: detect_excessive_calorie_deficit(metrics_7d),
        lambda: detect_low_activity(metrics_7d),
        lambda: detect_accumulated_fatigue(metrics_7d),
        lambda: detect_sleep_debt(metrics_7d),
        lambda: detect_dehydration_pattern(metrics_7d),
        lambda: detect_overtraining_risk(load_7d if load_7d > 0 else None, training_load_28d),
    ]

    for rule in rules:
        try:
            result = rule()
            if result:
                insights.append(result)
        except Exception:
            pass  # Isolement des erreurs de règle

    # Tri : critical > warning > info
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    insights.sort(key=lambda i: severity_order.get(i.severity, 3))

    return insights

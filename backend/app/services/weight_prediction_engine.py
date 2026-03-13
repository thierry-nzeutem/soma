"""
Weight Prediction Engine SOMA — LOT 10.

Prédit l'évolution du poids corporel sur 7, 14 et 30 jours en utilisant
un modèle énergétique linéaire avec facteurs d'adaptation métabolique.

Modèle : 7700 kcal de déficit/surplus = 1 kg de tissu adipeux.
Facteurs d'adaptation : le métabolisme s'adapte progressivement (−10%/14j, −20%/30j).

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional
from dataclasses import dataclass, field


# ── Constantes ─────────────────────────────────────────────────────────────────

KCAL_PER_KG = 7700.0           # kcal nécessaires pour ±1 kg de tissu adipeux

# Facteurs d'adaptation métabolique par horizon temporel
# Le corps s'adapte progressivement : réduction de la thermogenèse adaptative
_ADAPTATION: dict[int, float] = {
    7:  1.00,   # Court terme : pas d'adaptation significative
    14: 0.90,   # Adaptation modérée (−10%)
    30: 0.80,   # Adaptation marquée (−20%)
}

# Seuil en kg/semaine pour qualifier la tendance "stable"
_STABLE_THRESHOLD_KG = 0.3


# ── Dataclass résultat ─────────────────────────────────────────────────────────

@dataclass
class WeightPredictionResult:
    """Résultat complet des prédictions de poids corporel."""
    current_weight_kg: Optional[float] = None
    expected_weight_7d: Optional[float] = None
    expected_weight_14d: Optional[float] = None
    expected_weight_30d: Optional[float] = None
    daily_energy_balance_kcal: Optional[float] = None   # surplus(+) ou déficit(−)
    weekly_weight_change_kg: Optional[float] = None     # delta prévu à 7j
    trend_direction: str = "stable"                     # loss / gain / stable
    confidence: float = 0.0                             # 0–1
    assumptions: list = field(default_factory=list)


# ── Fonctions pures ────────────────────────────────────────────────────────────

def _compute_tdee(
    estimated_tdee_kcal: Optional[float],
    active_calories_kcal: Optional[float],
) -> Optional[float]:
    """
    Retourne la meilleure estimation de la dépense énergétique totale.
    Préfère le TDEE calculé par MetabolicTwin (plus précis).
    Fallback sur les calories actives si disponibles.
    """
    if estimated_tdee_kcal is not None and estimated_tdee_kcal > 0:
        return estimated_tdee_kcal
    if active_calories_kcal is not None and active_calories_kcal > 0:
        return active_calories_kcal
    return None


def _compute_delta_kg(
    daily_balance_kcal: float,
    days: int,
    adaptation_factor: float,
) -> float:
    """
    Calcule le delta de poids attendu (en kg) sur `days` jours.
    Intègre le facteur d'adaptation métabolique.

    delta = (balance × jours × adaptation) / 7700
    """
    return (daily_balance_kcal * days * adaptation_factor) / KCAL_PER_KG


def _trend_direction(weekly_delta_kg: float) -> str:
    """
    Classifie la tendance pondérale sur la base du delta à 7 jours.
    ±300g/semaine = stable, au-delà = perte ou gain.
    """
    if weekly_delta_kg < -_STABLE_THRESHOLD_KG:
        return "loss"
    if weekly_delta_kg > _STABLE_THRESHOLD_KG:
        return "gain"
    return "stable"


def _build_assumptions(
    using_tdee_estimate: bool,
    using_active_cal_fallback: bool,
    using_avg_calories: bool,
) -> list[str]:
    """Génère la liste des hypothèses du modèle pour transparence."""
    assumptions = [
        "Modèle linéaire : 7700 kcal ≈ 1 kg de tissu adipeux.",
        "Adaptation métabolique appliquée : −10 % à 14j, −20 % à 30j.",
    ]
    if using_tdee_estimate:
        assumptions.append("Dépense énergétique issue du Jumeau Métabolique (TDEE estimé).")
    elif using_active_cal_fallback:
        assumptions.append("Dépense énergétique approximée via les calories actives (moins précis).")
    if using_avg_calories:
        assumptions.append("Apport calorique : moyenne des 7 derniers jours disponibles.")
    assumptions.append("Les prédictions supposent un comportement alimentaire et d'activité constant.")
    return assumptions


# ── Fonction principale ────────────────────────────────────────────────────────

def compute_weight_predictions(
    current_weight_kg: Optional[float] = None,
    calories_consumed_avg: Optional[float] = None,  # moyenne des 7 derniers jours
    estimated_tdee_kcal: Optional[float] = None,
    active_calories_kcal: Optional[float] = None,
) -> WeightPredictionResult:
    """
    Calcule les prédictions de poids sur 7, 14 et 30 jours.

    Paramètres
    ----------
    current_weight_kg : poids actuel (kg)
    calories_consumed_avg : apport calorique moyen sur 7j (kcal/j)
    estimated_tdee_kcal : dépense totale estimée par MetabolicTwin (kcal/j)
    active_calories_kcal : calories actives alternatives (kcal/j)

    Retourne
    --------
    WeightPredictionResult avec prédictions 7/14/30j, tendance et confidence.
    Retourne confidence=0.0 si le poids actuel ou le bilan énergétique est absent.
    """
    # ── Confidence tracking ────────────────────────────────────────────────────
    confidence = 0.0
    using_tdee_estimate = False
    using_active_cal_fallback = False
    using_avg_calories = False

    # ── TDEE ──────────────────────────────────────────────────────────────────
    tdee = _compute_tdee(estimated_tdee_kcal, active_calories_kcal)
    if tdee is not None:
        confidence += 0.35
        using_tdee_estimate = (estimated_tdee_kcal is not None and estimated_tdee_kcal > 0)
        using_active_cal_fallback = not using_tdee_estimate

    # ── Apport calorique ───────────────────────────────────────────────────────
    if calories_consumed_avg is not None and calories_consumed_avg > 0:
        confidence += 0.35
        using_avg_calories = True

    # ── Poids actuel ──────────────────────────────────────────────────────────
    if current_weight_kg is not None and current_weight_kg > 0:
        confidence += 0.30

    confidence = round(min(1.0, confidence), 2)

    # ── Impossibilité de calculer ─────────────────────────────────────────────
    if current_weight_kg is None or current_weight_kg <= 0:
        return WeightPredictionResult(
            current_weight_kg=current_weight_kg,
            confidence=0.0,
            assumptions=["Poids actuel manquant — impossible de calculer les prédictions."],
        )

    if tdee is None or calories_consumed_avg is None:
        return WeightPredictionResult(
            current_weight_kg=round(current_weight_kg, 2),
            confidence=0.0,
            assumptions=[
                "Données énergétiques manquantes (TDEE ou apport calorique).",
                "Enregistrez vos repas et synchronisez vos données d'activité.",
            ],
        )

    # ── Calcul du bilan énergétique ────────────────────────────────────────────
    daily_balance = round(calories_consumed_avg - tdee, 1)

    # ── Prédictions par horizon ────────────────────────────────────────────────
    weight_7d = round(
        current_weight_kg + _compute_delta_kg(daily_balance, 7, _ADAPTATION[7]), 2
    )
    weight_14d = round(
        current_weight_kg + _compute_delta_kg(daily_balance, 14, _ADAPTATION[14]), 2
    )
    weight_30d = round(
        current_weight_kg + _compute_delta_kg(daily_balance, 30, _ADAPTATION[30]), 2
    )

    weekly_delta = round(weight_7d - current_weight_kg, 3)
    trend = _trend_direction(weekly_delta)
    assumptions = _build_assumptions(using_tdee_estimate, using_active_cal_fallback, using_avg_calories)

    return WeightPredictionResult(
        current_weight_kg=round(current_weight_kg, 2),
        expected_weight_7d=weight_7d,
        expected_weight_14d=weight_14d,
        expected_weight_30d=weight_30d,
        daily_energy_balance_kcal=daily_balance,
        weekly_weight_change_kg=weekly_delta,
        trend_direction=trend,
        confidence=confidence,
        assumptions=assumptions,
    )

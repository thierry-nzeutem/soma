"""
Longevity Engine SOMA — LOT 3.

Calcule le score de longévité multi-dimensionnel basé sur 7 composantes.
Inspiré des recherches en médecine préventive (VO2max, sommeil, nutrition,
régularité, composition corporelle).

Score final : moyenne pondérée des composantes disponibles (0-100).
Âge biologique estimé : basé sur l'écart au score optimal (75/100).

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass


# ── Poids des composantes ──────────────────────────────────────────────────────

COMPONENT_WEIGHTS: Dict[str, float] = {
    "cardio_score":     0.20,
    "strength_score":   0.20,
    "sleep_score":      0.15,
    "nutrition_score":  0.15,
    "weight_score":     0.15,
    "body_comp_score":  0.00,  # Optionnel : bonus si masse musculaire disponible
    "consistency_score": 0.15,
}

# Age biologique : référence = score 75/100 → age biologique = age réel
# Chaque 5 points en moins = +1 an biologique estimé
LONGEVITY_OPTIMAL_SCORE = 75.0
AGE_YEARS_PER_SCORE_POINT = 0.2   # 0.2 an / point


# ── Fonctions de scoring ────────────────────────────────────────────────────────

def score_cardio(
    steps: Optional[float],            # pas/jour (moyenne 30j)
    hrv_ms: Optional[float],           # HRV moyen (ms)
    active_calories: Optional[float],  # kcal/jour actives (moyenne 30j)
    workout_frequency_pct: Optional[float],  # % jours avec activité (30j)
) -> Optional[float]:
    """
    Score cardio (0-100) basé sur plusieurs indicateurs.
    - Pas : 10 000 pas/j = 100, 0 pas = 0
    - HRV : > 70ms = excellent, < 20ms = faible
    - Activité : présence et régularité
    """
    sub_scores = []

    if steps is not None:
        step_score = min(100, (steps / 10_000) * 100)
        sub_scores.append(step_score)

    if hrv_ms is not None:
        hrv_score = max(0, min(100, (hrv_ms - 20) / (70 - 20) * 100))
        sub_scores.append(hrv_score)

    if active_calories is not None:
        cal_score = min(100, (active_calories / 500) * 100)
        sub_scores.append(cal_score)

    if workout_frequency_pct is not None:
        # 4 séances/7j = 57% → 100 points, 1/7 = 14% → 30 points
        freq_score = min(100, workout_frequency_pct * 1.5)
        sub_scores.append(freq_score)

    if not sub_scores:
        return None
    return round(sum(sub_scores) / len(sub_scores), 1)


def score_strength(
    total_tonnage_avg: Optional[float],   # tonnage moyen par séance (kg)
    workout_count_30d: Optional[int],     # séances sur 30j
) -> Optional[float]:
    """
    Score force (0-100) basé sur le volume d'entraînement.
    - Tonnage : 3000 kg/séance = 100, 0 = 0
    - Régularité : 12 séances/30j (3/sem) = 100
    """
    sub_scores = []

    if total_tonnage_avg is not None and total_tonnage_avg >= 0:
        tonnage_score = min(100, (total_tonnage_avg / 3000) * 100)
        sub_scores.append(tonnage_score)

    if workout_count_30d is not None:
        freq_score = min(100, (workout_count_30d / 12) * 100)
        sub_scores.append(freq_score)

    if not sub_scores:
        return None
    return round(sum(sub_scores) / len(sub_scores), 1)


def score_sleep(
    avg_sleep_hours: Optional[float],     # heures de sommeil moyennes (30j)
    avg_sleep_quality: Optional[float],   # score qualité moyen (0-100)
) -> Optional[float]:
    """
    Score sommeil (0-100).
    - Durée : 8h = 100, < 5h = 0, courbe en cloche (trop dormir = moins bon)
    - Qualité perçue (si disponible)
    """
    sub_scores = []

    if avg_sleep_hours is not None:
        # Optimal : 7-9h → 100. < 5h ou > 10h = dégradé
        if avg_sleep_hours >= 7 and avg_sleep_hours <= 9:
            dur_score = 100
        elif avg_sleep_hours >= 5 and avg_sleep_hours < 7:
            dur_score = max(0, ((avg_sleep_hours - 5) / 2) * 80)
        elif avg_sleep_hours > 9:
            dur_score = max(60, 100 - (avg_sleep_hours - 9) * 20)
        else:
            dur_score = 0
        sub_scores.append(round(dur_score, 1))

    if avg_sleep_quality is not None:
        sub_scores.append(avg_sleep_quality)

    if not sub_scores:
        return None
    return round(sum(sub_scores) / len(sub_scores), 1)


def score_nutrition(
    avg_calories_pct: Optional[float],   # % cible calories atteint (30j)
    avg_protein_pct: Optional[float],    # % cible protéines atteint
    meal_frequency_pct: Optional[float], # % jours avec au moins 1 entrée
    micro_score: Optional[float],        # score micronutritionnel (0-100)
) -> Optional[float]:
    """
    Score nutrition (0-100).
    Combine : conformité calorique, protéique, régularité du suivi, micronutriments.
    """
    sub_scores = []

    if avg_calories_pct is not None:
        # 90-110% de la cible = 100
        if 0.90 <= avg_calories_pct <= 1.10:
            cal_score = 100
        elif avg_calories_pct < 0.90:
            cal_score = max(0, avg_calories_pct / 0.90 * 100)
        else:
            cal_score = max(50, 100 - (avg_calories_pct - 1.10) * 100)
        sub_scores.append(round(cal_score, 1))

    if avg_protein_pct is not None:
        prot_score = min(100, avg_protein_pct * 100)
        sub_scores.append(round(prot_score, 1))

    if meal_frequency_pct is not None:
        sub_scores.append(round(min(100, meal_frequency_pct), 1))

    if micro_score is not None:
        sub_scores.append(micro_score)

    if not sub_scores:
        return None
    return round(sum(sub_scores) / len(sub_scores), 1)


def score_weight(
    bmi: Optional[float],
    weight_trend_kg: Optional[float],     # delta poids sur 30j (kg)
    goal: Optional[str],
) -> Optional[float]:
    """
    Score poids/IMC (0-100).
    - IMC optimal 20-24.9 = 100
    - Tendance : en accord avec l'objectif = bonus
    """
    if bmi is None:
        return None

    # Score IMC
    if 20 <= bmi <= 24.9:
        bmi_score = 100
    elif 18.5 <= bmi < 20:
        bmi_score = 80 + (bmi - 18.5) / 1.5 * 20
    elif 25 <= bmi <= 27:
        bmi_score = 100 - (bmi - 25) / 2 * 30
    elif 27 < bmi <= 30:
        bmi_score = 70 - (bmi - 27) / 3 * 30
    elif bmi > 30:
        bmi_score = max(10, 40 - (bmi - 30) * 3)
    else:
        bmi_score = max(10, 40 - (18.5 - bmi) * 10)

    # Bonus tendance en accord avec l'objectif
    trend_bonus = 0
    if weight_trend_kg is not None and goal:
        if goal == "weight_loss" and weight_trend_kg < -0.1:
            trend_bonus = 5
        elif goal == "muscle_gain" and weight_trend_kg > 0.1:
            trend_bonus = 5
        elif goal == "maintenance" and abs(weight_trend_kg) < 0.5:
            trend_bonus = 5

    return round(min(100, bmi_score + trend_bonus), 1)


def score_body_composition(
    body_fat_pct: Optional[float],
    sex: Optional[str],
) -> Optional[float]:
    """
    Score composition corporelle (0-100) si données disponibles.
    Basé sur le % de graisse corporelle.
    """
    if body_fat_pct is None:
        return None

    # Normes par sexe (ACSM)
    if sex and sex.lower() == "female":
        # Fitness : 21-24%, Athletic : 14-20%, Excellent : < 14%
        if body_fat_pct <= 14:
            score = 100
        elif body_fat_pct <= 20:
            score = 100 - (body_fat_pct - 14) / 6 * 20
        elif body_fat_pct <= 24:
            score = 80 - (body_fat_pct - 20) / 4 * 20
        elif body_fat_pct <= 31:
            score = max(30, 60 - (body_fat_pct - 24) / 7 * 30)
        else:
            score = max(10, 30 - (body_fat_pct - 31) * 2)
    else:
        # Fitness : 14-17%, Athletic : 6-13%, Excellent : < 6%
        if body_fat_pct <= 6:
            score = 100
        elif body_fat_pct <= 13:
            score = 100 - (body_fat_pct - 6) / 7 * 20
        elif body_fat_pct <= 17:
            score = 80 - (body_fat_pct - 13) / 4 * 20
        elif body_fat_pct <= 24:
            score = max(30, 60 - (body_fat_pct - 17) / 7 * 30)
        else:
            score = max(10, 30 - (body_fat_pct - 24) * 2)

    return round(max(0, min(100, score)), 1)


def score_consistency(
    tracking_days_pct: Optional[float],      # % jours avec données (30j)
    workout_streak: Optional[int] = None,    # jours consécutifs avec activité
) -> Optional[float]:
    """
    Score régularité (0-100).
    La régularité est un prédicteur majeur de succès à long terme.
    """
    sub_scores = []

    if tracking_days_pct is not None:
        sub_scores.append(min(100, tracking_days_pct))

    if workout_streak is not None:
        streak_score = min(100, (workout_streak / 14) * 100)  # 14j consécutifs = 100
        sub_scores.append(streak_score)

    if not sub_scores:
        return None
    return round(sum(sub_scores) / len(sub_scores), 1)


@dataclass
class LongevityResult:
    """Résultat complet du calcul du score de longévité."""
    cardio_score: Optional[float]
    strength_score: Optional[float]
    sleep_score: Optional[float]
    nutrition_score: Optional[float]
    weight_score: Optional[float]
    body_comp_score: Optional[float]
    consistency_score: Optional[float]
    longevity_score: float                  # 0-100
    biological_age_estimate: Optional[float]
    top_improvement_levers: Dict[str, Any]
    confidence: float                       # 0-1 (proportion de composantes disponibles)


def compute_longevity_score(
    actual_age: Optional[float],
    # Cardio
    avg_steps: Optional[float] = None,
    avg_hrv_ms: Optional[float] = None,
    avg_active_calories: Optional[float] = None,
    workout_frequency_pct: Optional[float] = None,
    # Force
    avg_tonnage_per_session: Optional[float] = None,
    workout_count_30d: Optional[int] = None,
    # Sommeil
    avg_sleep_hours: Optional[float] = None,
    avg_sleep_quality_score: Optional[float] = None,
    # Nutrition
    avg_calories_pct_target: Optional[float] = None,
    avg_protein_pct_target: Optional[float] = None,
    meal_tracking_pct: Optional[float] = None,
    micro_score: Optional[float] = None,
    # Poids
    bmi: Optional[float] = None,
    weight_trend_kg_30d: Optional[float] = None,
    goal: Optional[str] = None,
    # Composition corporelle
    body_fat_pct: Optional[float] = None,
    sex: Optional[str] = None,
    # Régularité
    tracking_days_pct: Optional[float] = None,
) -> LongevityResult:
    """
    Calcule le score de longévité multi-dimensionnel.

    Retourne un LongevityResult avec les scores par composante,
    le score global, l'âge biologique estimé et les leviers d'amélioration.
    """
    # Calcul des composantes
    cardio = score_cardio(avg_steps, avg_hrv_ms, avg_active_calories, workout_frequency_pct)
    strength = score_strength(avg_tonnage_per_session, workout_count_30d)
    sleep = score_sleep(avg_sleep_hours, avg_sleep_quality_score)
    nutrition = score_nutrition(avg_calories_pct_target, avg_protein_pct_target,
                                meal_tracking_pct, micro_score)
    weight = score_weight(bmi, weight_trend_kg_30d, goal)
    body_comp = score_body_composition(body_fat_pct, sex)
    consistency = score_consistency(tracking_days_pct)

    # Score global pondéré
    scores = {
        "cardio_score": cardio,
        "strength_score": strength,
        "sleep_score": sleep,
        "nutrition_score": nutrition,
        "weight_score": weight,
        "consistency_score": consistency,
    }
    # body_comp est un bonus (poids 0 par défaut, activé si disponible)
    if body_comp is not None:
        scores["body_comp_score"] = body_comp
        weights = {**COMPONENT_WEIGHTS, "body_comp_score": 0.10}
        # Rééquilibrer les autres
        for k in ["cardio_score", "strength_score", "nutrition_score", "weight_score", "consistency_score"]:
            weights[k] = max(0, weights[k] - 0.02)
    else:
        weights = COMPONENT_WEIGHTS.copy()

    available = {k: v for k, v in scores.items() if v is not None}
    if not available:
        longevity_score = 0.0
        confidence = 0.0
    else:
        total_w = sum(weights[k] for k in available)
        if total_w > 0:
            longevity_score = sum(available[k] * weights[k] for k in available) / total_w
        else:
            longevity_score = sum(available.values()) / len(available)
        longevity_score = round(min(100, longevity_score), 1)
        confidence = round(total_w, 2)

    # Âge biologique
    bio_age = None
    if actual_age and longevity_score > 0:
        delta = (longevity_score - LONGEVITY_OPTIMAL_SCORE) * AGE_YEARS_PER_SCORE_POINT
        bio_age = round(actual_age - delta, 1)

    # Leviers d'amélioration (composantes avec score < 70)
    levers = {}
    component_labels = {
        "cardio_score": "Activité cardiovasculaire",
        "strength_score": "Entraînement de force",
        "sleep_score": "Qualité du sommeil",
        "nutrition_score": "Nutrition",
        "weight_score": "Gestion du poids",
        "body_comp_score": "Composition corporelle",
        "consistency_score": "Régularité",
    }
    for key, val in scores.items():
        if val is not None and val < 70:
            levers[component_labels.get(key, key)] = round(val, 1)
    # Tri par score croissant (priorité aux plus faibles)
    levers = dict(sorted(levers.items(), key=lambda x: x[1]))

    return LongevityResult(
        cardio_score=cardio,
        strength_score=strength,
        sleep_score=sleep,
        nutrition_score=nutrition,
        weight_score=weight,
        body_comp_score=body_comp,
        consistency_score=consistency,
        longevity_score=longevity_score,
        biological_age_estimate=bio_age,
        top_improvement_levers=levers,
        confidence=confidence,
    )

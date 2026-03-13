"""
Nutrition Engine SOMA — LOT 3.

Calcule les besoins nutritionnels personnalisés du jour.
Étend les calculs de base (calculations.py) avec :
  - Ajustement entraînement du jour
  - Répartition glucides/lipides cohérente
  - Support jeûne intermittent (fenêtre de consommation)
  - Cibles fibres (14g/1000 kcal selon IOM)

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional
from dataclasses import dataclass

from app.services.calculations import (
    calculate_bmr_mifflin,
    calculate_tdee,
    calculate_protein_target,
    calculate_calorie_target,
    calculate_hydration_target,
    ACTIVITY_MULTIPLIERS,
)


# ── Constantes ─────────────────────────────────────────────────────────────────

# Calories supplémentaires par type d'entraînement (par heure)
WORKOUT_CALORIE_BONUS: dict = {
    "strength": 250,    # kcal/h — force (métabolisme post-exercice élevé)
    "cardio": 400,      # kcal/h — cardio intensif
    "hiit": 450,        # kcal/h — HIIT
    "mobility": 100,    # kcal/h — mobilité / yoga
    "mixed": 300,       # kcal/h — crossfit / circuits
    "default": 200,     # kcal/h — défaut
}

FAT_RATIO_BY_GOAL = {
    "weight_loss": 0.30,     # 30% des calories en lipides (régime modéré en graisses)
    "muscle_gain": 0.25,     # 25% — priorité glucides pour l'anabolisme
    "maintenance": 0.28,     # 28% — équilibré
    "performance": 0.25,     # 25% — glucides prioritaires
    "longevity": 0.35,       # 35% — lipides sains (méditerranéen)
}

# Calories par gramme de macronutriment
KCAL_PER_G = {"protein": 4.0, "carbs": 4.0, "fat": 9.0}

FIBER_PER_1000_KCAL = 14.0  # g/1000 kcal (recommandation IOM)

FASTING_WINDOW_HOURS: dict = {
    "16:8": 8.0,
    "18:6": 6.0,
    "20:4": 4.0,
    "23:1": 1.0,
    "OMAD": 1.0,
}


# ── Dataclass résultat ─────────────────────────────────────────────────────────

@dataclass
class NutritionTargets:
    """Cibles nutritionnelles personnalisées pour la journée."""
    calories_target: float
    protein_target_g: float
    carbs_target_g: float
    fat_target_g: float
    fiber_target_g: float
    hydration_target_ml: float

    # Répartition macros (%)
    protein_pct: float
    carbs_pct: float
    fat_pct: float

    # Contexte
    base_tdee_kcal: float
    workout_bonus_kcal: float
    goal_adjustment_kcal: float
    target_mode: str   # standard | training_day | rest_day | fasting

    # Timing jeûne
    eating_window_hours: Optional[float] = None
    fasting_start_at: Optional[str] = None

    reasoning: str = ""


# ── Fonctions pures ────────────────────────────────────────────────────────────

def compute_workout_calorie_bonus(
    workout_type: Optional[str],
    duration_minutes: Optional[float],
    rpe_score: Optional[float],
) -> float:
    """
    Estime les calories supplémentaires liées à l'entraînement du jour.
    Formule : bonus_horaire × durée × facteur_intensité(RPE)
    """
    if not duration_minutes or duration_minutes <= 0:
        return 0.0

    base_per_hour = WORKOUT_CALORIE_BONUS.get(
        (workout_type or "default").lower(), WORKOUT_CALORIE_BONUS["default"]
    )

    # Facteur intensité : RPE 5 = 1.0, RPE 10 = 1.4
    rpe_factor = 1.0
    if rpe_score:
        rpe_factor = max(0.7, min(1.5, 0.7 + (rpe_score / 10) * 0.8))

    duration_h = duration_minutes / 60.0
    return round(base_per_hour * duration_h * rpe_factor, 0)


def compute_fat_target_g(calories_target: float, goal: Optional[str]) -> float:
    """Calcule la cible lipides en grammes depuis le ratio calories/goal."""
    ratio = FAT_RATIO_BY_GOAL.get(goal or "maintenance", 0.28)
    fat_kcal = calories_target * ratio
    return round(fat_kcal / KCAL_PER_G["fat"], 1)


def compute_carbs_target_g(
    calories_target: float,
    protein_g: float,
    fat_g: float,
) -> float:
    """
    Glucides résiduels après allocation protéines + lipides.
    Glucides restants = (calories - énergie_protéines - énergie_lipides) / 4
    """
    protein_kcal = protein_g * KCAL_PER_G["protein"]
    fat_kcal = fat_g * KCAL_PER_G["fat"]
    carbs_kcal = max(0, calories_target - protein_kcal - fat_kcal)
    return round(carbs_kcal / KCAL_PER_G["carbs"], 1)


def compute_fiber_target_g(calories_target: float) -> float:
    """Fibres : 14g par 1000 kcal (recommandation IOM 2002)."""
    return round((calories_target / 1000.0) * FIBER_PER_1000_KCAL, 1)


def compute_macro_percentages(
    calories_target: float,
    protein_g: float,
    carbs_g: float,
    fat_g: float,
) -> tuple[float, float, float]:
    """Retourne (protein_pct, carbs_pct, fat_pct) exprimés en % de l'énergie."""
    if calories_target <= 0:
        return 0.0, 0.0, 0.0
    protein_pct = round((protein_g * KCAL_PER_G["protein"]) / calories_target * 100, 1)
    fat_pct = round((fat_g * KCAL_PER_G["fat"]) / calories_target * 100, 1)
    carbs_pct = round(100 - protein_pct - fat_pct, 1)
    return protein_pct, carbs_pct, fat_pct


def compute_fasting_window(
    fasting_protocol: Optional[str],
    usual_wake_time_str: Optional[str] = None,
) -> tuple[Optional[float], Optional[str]]:
    """
    Calcule la fenêtre alimentaire et l'heure de début du jeûne.
    Retourne (window_hours, fasting_start_at).
    """
    if not fasting_protocol:
        return None, None

    window_h = FASTING_WINDOW_HOURS.get(fasting_protocol)
    if not window_h:
        return None, None

    # Si réveil connu, calcule l'heure de début du jeûne (dernier repas)
    fasting_start = None
    if usual_wake_time_str and ":" in str(usual_wake_time_str):
        try:
            parts = str(usual_wake_time_str).split(":")
            wake_h = int(parts[0])
            # Début alimentation = heure de réveil (ex: 7h)
            # Fin alimentation = réveil + window_h (ex: 7 + 8 = 15h)
            # Début jeûne = fin alimentation (ex: 15h)
            end_eating_h = (wake_h + window_h) % 24
            fasting_start = f"{int(end_eating_h):02d}:00"
        except Exception:
            pass

    return window_h, fasting_start


def compute_nutrition_targets(
    # Profil
    age: Optional[int],
    sex: Optional[str],            # "male" | "female" | "other"
    height_cm: Optional[float],
    weight_kg: Optional[float],
    body_fat_pct: Optional[float],
    activity_level: Optional[str],
    fitness_level: Optional[str],
    primary_goal: Optional[str],
    # Nutrition préférences
    dietary_regime: Optional[str] = None,
    intermittent_fasting: bool = False,
    fasting_protocol: Optional[str] = None,
    usual_wake_time: Optional[str] = None,
    # Entraînement du jour
    workout_type: Optional[str] = None,
    workout_duration_minutes: Optional[float] = None,
    workout_rpe: Optional[float] = None,
    # Saison (pour hydratation)
    season: Optional[str] = None,
) -> NutritionTargets:
    """
    Calcule les besoins nutritionnels personnalisés du jour.

    Workflow :
    1. BMR Mifflin-St Jeor (ou Katch-McCardle si body_fat connu)
    2. TDEE = BMR × multiplicateur activité
    3. Bonus entraînement du jour
    4. Ajustement objectif (déficit / surplus)
    5. Protéines → Lipides → Glucides résiduels
    6. Fibres (14g / 1000 kcal)
    7. Hydratation (33ml/kg + activité + saison)
    """
    # Valeurs par défaut robustes
    w = weight_kg or 75.0
    h = height_cm or 175.0
    a = age or 35
    s = sex or "male"
    goal = primary_goal or "maintenance"
    level = activity_level or "moderate"
    fit = fitness_level or "intermediate"

    # 1. BMR
    bmr = calculate_bmr_mifflin(w, h, a, s)

    # 2. TDEE
    tdee = calculate_tdee(bmr, level)

    # 3. Bonus entraînement
    workout_bonus = compute_workout_calorie_bonus(workout_type, workout_duration_minutes, workout_rpe)

    # 4. Ajustement objectif
    cal_target, cal_reason = calculate_calorie_target(tdee, goal, w, None)
    goal_adjustment = cal_target - tdee  # négatif = déficit, positif = surplus

    # Ajouter le bonus entraînement
    final_cal_target = round(cal_target + workout_bonus, 0)

    # 5. Protéines (body_fat_pct géré en interne par calculate_protein_target)
    prot_min, prot_max, prot_reason = calculate_protein_target(
        w, goal, fit, body_fat_pct=body_fat_pct
    )
    protein_g = round((prot_min + prot_max) / 2, 1)

    # 6. Lipides
    fat_g = compute_fat_target_g(final_cal_target, goal)

    # 7. Glucides résiduels
    carbs_g = compute_carbs_target_g(final_cal_target, protein_g, fat_g)

    # 8. Fibres
    fiber_g = compute_fiber_target_g(final_cal_target)

    # 9. Hydratation
    hydration_ml, _ = calculate_hydration_target(w, level, season)

    # 10. Répartition %
    protein_pct, carbs_pct, fat_pct = compute_macro_percentages(
        final_cal_target, protein_g, carbs_g, fat_g
    )

    # 11. Mode cible
    if workout_bonus > 0:
        mode = "training_day"
    elif intermittent_fasting:
        mode = "fasting"
    else:
        mode = "standard"

    # 12. Jeûne intermittent
    eating_window_h, fasting_start = (None, None)
    if intermittent_fasting:
        eating_window_h, fasting_start = compute_fasting_window(fasting_protocol, usual_wake_time)

    # Reasoning synthétique
    parts = [
        f"BMR {round(bmr)} kcal × {ACTIVITY_MULTIPLIERS.get(level, 1.55):.3f} ({level}) = TDEE {round(tdee)} kcal.",
        cal_reason,
    ]
    if workout_bonus > 0:
        parts.append(f"Bonus entraînement {workout_type or 'default'} ({round(workout_duration_minutes or 0)} min) : +{int(workout_bonus)} kcal.")
    if intermittent_fasting and fasting_protocol:
        parts.append(f"Jeûne {fasting_protocol} : fenêtre de {eating_window_h}h.")
    reasoning = " ".join(parts)

    return NutritionTargets(
        calories_target=final_cal_target,
        protein_target_g=protein_g,
        carbs_target_g=carbs_g,
        fat_target_g=fat_g,
        fiber_target_g=fiber_g,
        hydration_target_ml=hydration_ml,
        protein_pct=protein_pct,
        carbs_pct=carbs_pct,
        fat_pct=fat_pct,
        base_tdee_kcal=round(tdee, 0),
        workout_bonus_kcal=workout_bonus,
        goal_adjustment_kcal=goal_adjustment,
        target_mode=mode,
        eating_window_hours=eating_window_h,
        fasting_start_at=fasting_start,
        reasoning=reasoning,
    )

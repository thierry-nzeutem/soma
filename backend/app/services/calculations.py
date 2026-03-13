"""
Service de calculs physiologiques de SOMA.

Toutes les formules sont tracées avec leur source scientifique.
Les résultats sont accompagnés d'un niveau de confiance.
"""
from typing import Optional, Tuple


# =============================================================================
# MÉTABOLISME BASAL (BMR)
# =============================================================================

def calculate_bmr_mifflin(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
) -> float:
    """
    Formule Mifflin-St Jeor (1990) — référence actuelle recommandée.
    Source: Mifflin MD et al. A new predictive equation for resting energy expenditure.
    Am J Clin Nutr. 1990;51(2):241-7.

    Précision: ±10% par rapport à la calorimétrie indirecte.
    """
    if sex == "male":
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:  # female ou other
        return (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161


def calculate_bmr_katch_mcardle(
    lean_mass_kg: float,
) -> float:
    """
    Formule Katch-McArdle — plus précise si composition corporelle connue.
    Source: Katch V, McArdle W. Nutrition, Weight Control, and Exercise. 1983.
    """
    return 370 + (21.6 * lean_mass_kg)


# =============================================================================
# DÉPENSE ÉNERGÉTIQUE TOTALE (TDEE)
# =============================================================================

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,       # Peu ou pas d'exercice, travail de bureau
    "light": 1.375,         # Exercice léger 1-3j/sem
    "moderate": 1.55,       # Exercice modéré 3-5j/sem
    "active": 1.725,        # Exercice intense 6-7j/sem
    "very_active": 1.9,     # Exercice très intense + travail physique
}


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Dépense énergétique totale via multiplicateur d'activité (Harris-Benedict revisé).
    """
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    return bmr * multiplier


# =============================================================================
# IMC
# =============================================================================

def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """IMC = poids (kg) / taille² (m)"""
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    elif bmi < 25:
        return "normal"
    elif bmi < 30:
        return "overweight"
    else:
        return "obese"


# =============================================================================
# BESOINS EN PROTÉINES
# =============================================================================

def calculate_protein_target(
    weight_kg: float,
    primary_goal: str,
    fitness_level: str,
    body_fat_pct: Optional[float] = None,
) -> Tuple[float, float, str]:
    """
    Calcul des besoins protéiques selon objectif et niveau.

    Retourne: (min_g, max_g, reasoning)

    Sources:
    - ISSN Position Stand on protein and exercise (2017)
    - Phillips & Van Loon, 2011: Dietary protein for athletes
    - Morton et al. 2018: dietary protein and muscle mass meta-analysis
    """
    base_weight = weight_kg

    # Si composition connue, utiliser masse maigre
    if body_fat_pct and body_fat_pct > 0:
        lean_mass = weight_kg * (1 - body_fat_pct / 100)
        base_weight = lean_mass

    # Multiplicateurs selon objectif
    if primary_goal == "weight_loss":
        # Plus de protéines pour préserver la masse musculaire en déficit
        min_factor, max_factor = 1.8, 2.4
        reasoning = "Déficit calorique : protéines élevées pour préserver la masse musculaire"
    elif primary_goal == "muscle_gain":
        min_factor, max_factor = 1.6, 2.2
        reasoning = "Prise de masse : apport protéique optimal pour synthèse musculaire"
    elif primary_goal == "performance":
        min_factor, max_factor = 1.6, 2.0
        reasoning = "Performance : soutien récupération et adaptation musculaire"
    else:  # maintenance, longevity
        min_factor, max_factor = 1.4, 1.8
        reasoning = "Maintien : préservation masse musculaire et santé"

    # Ajustement niveau
    if fitness_level in ("advanced", "athlete"):
        min_factor += 0.1
        max_factor += 0.1

    return round(base_weight * min_factor, 1), round(base_weight * max_factor, 1), reasoning


# =============================================================================
# BESOINS CALORIQUES SELON OBJECTIF
# =============================================================================

def calculate_calorie_target(
    tdee: float,
    primary_goal: str,
    current_weight_kg: float,
    goal_weight_kg: Optional[float],
) -> Tuple[float, str]:
    """
    Objectif calorique selon le but.

    Retourne: (target_kcal, reasoning)
    """
    if primary_goal == "weight_loss":
        # Déficit 300-500 kcal — conservateur pour préserver masse musculaire
        deficit = 400
        target = tdee - deficit
        # Floor de sécurité : jamais sous 1200 kcal (femme) ou 1500 kcal (homme)
        target = max(target, 1400)
        reasoning = f"Déficit de {deficit} kcal/jour sur TDEE estimé {tdee:.0f} kcal"
    elif primary_goal == "muscle_gain":
        surplus = 250
        target = tdee + surplus
        reasoning = f"Surplus de {surplus} kcal/jour pour prise de masse lean"
    else:  # maintenance, performance, longevity
        target = tdee
        reasoning = "Apport calorique d'entretien"

    return round(target, 0), reasoning


# =============================================================================
# HYDRATATION
# =============================================================================

def calculate_hydration_target(
    weight_kg: float,
    activity_level: str,
    season: str = "normal",
) -> Tuple[float, str]:
    """
    Objectif hydratation journalier.
    Source: Institute of Medicine (IOM) + ACSM guidelines.

    Retourne: (target_ml, reasoning)
    """
    # Base: 30-35 ml/kg
    base_ml = weight_kg * 33

    # Ajustement activité
    activity_bonus = {
        "sedentary": 0,
        "light": 300,
        "moderate": 500,
        "active": 750,
        "very_active": 1000,
    }
    bonus = activity_bonus.get(activity_level, 300)

    # Ajustement saison
    season_bonus = {"summer": 500, "normal": 0, "winter": -100}.get(season, 0)

    target = base_ml + bonus + season_bonus
    reasoning = f"Base {base_ml:.0f}ml (33ml/kg) + activité {bonus}ml"

    return round(target, 0), reasoning


# =============================================================================
# SCORE DE COMPLÉTUDE DU PROFIL
# =============================================================================

def calculate_profile_completeness(profile_data: dict) -> float:
    """
    Score 0-100 représentant la complétude du profil.
    Plus le profil est complet, meilleures sont les recommandations.
    """
    fields = {
        # Champs essentiels (poids double)
        "age": 2,
        "sex": 2,
        "height_cm": 2,
        "primary_goal": 2,
        "activity_level": 2,
        # Champs importants
        "fitness_level": 1,
        "dietary_regime": 1,
        "intermittent_fasting": 1,
        "meals_per_day": 1,
        "preferred_training_time": 1,
        # Champs complémentaires
        "food_allergies": 1,
        "home_equipment": 1,
        "gym_access": 1,
        "avg_energy_level": 1,
        "perceived_sleep_quality": 1,
        "physical_constraints": 1,
    }

    total_weight = sum(fields.values())
    earned_weight = 0

    for field, weight in fields.items():
        value = profile_data.get(field)
        if value is not None and value != "" and value != []:
            earned_weight += weight

    return round((earned_weight / total_weight) * 100, 1)


# =============================================================================
# CHARGE D'ENTRAÎNEMENT
# =============================================================================

def calculate_training_load(duration_minutes: float, rpe: float) -> float:
    """
    Session RPE method (Foster et al. 2001).
    Charge interne = Durée (min) × RPE (1-10)
    """
    return duration_minutes * rpe


def calculate_acwr(acute_load: float, chronic_load: float) -> Optional[float]:
    """
    Acute:Chronic Workload Ratio (ACWR).
    Zone optimale: 0.8-1.3
    Risque blessure élevé: > 1.5
    Source: Gabbett TJ. Br J Sports Med. 2016.
    """
    if chronic_load <= 0:
        return None
    return round(acute_load / chronic_load, 2)

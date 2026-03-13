"""
Health Plan Service SOMA — LOT 3.

Génère le plan santé quotidien personnalisé ("morning briefing").
Agrège readiness, nutrition cibles, activité et alertes pour créer
un plan d'action concret pour la journée.

Pas de DB directe — reçoit les données en paramètre (composition de services).
Toutes les fonctions sont pures et testables.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.services.nutrition_engine import NutritionTargets, FASTING_WINDOW_HOURS


# ── Paramètres par défaut ─────────────────────────────────────────────────────

SLEEP_TARGET_HOURS = 8.0
STEPS_DAILY_GOAL = 8_000


# ── Dataclass plan ─────────────────────────────────────────────────────────────

@dataclass
class DailyHealthPlan:
    """Plan santé journalier structuré."""
    date: str
    generated_at: datetime

    # Séance recommandée
    workout_recommendation: Dict[str, Any]

    # Objectifs du jour
    protein_target_g: float
    calorie_target: float
    hydration_target_ml: float
    steps_goal: int
    sleep_target_hours: float

    # Récupération
    readiness_level: str       # excellent | good | fair | poor
    recommended_intensity: str

    # Alertes
    alerts: List[Dict[str, str]] = field(default_factory=list)

    # Conseils
    daily_tips: List[str] = field(default_factory=list)

    # Fenêtre alimentaire
    eating_window: Optional[Dict[str, Any]] = None

    # Focus nutritionnel du jour
    nutrition_focus: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _readiness_level(score: Optional[float]) -> str:
    """Traduit un score de readiness en niveau qualitatif."""
    if score is None:
        return "unknown"
    if score >= 80:
        return "excellent"
    if score >= 65:
        return "good"
    if score >= 50:
        return "fair"
    return "poor"


def _build_workout_recommendation(
    intensity: str,
    has_workout_today: bool,
    primary_goal: Optional[str],
    fitness_level: Optional[str],
    home_equipment: Optional[list],
    gym_access: bool = False,
) -> Dict[str, Any]:
    """Construit la recommandation de séance du jour."""
    if has_workout_today:
        return {
            "type": "already_done",
            "message": "Séance du jour déjà réalisée. Récupération active recommandée.",
            "intensity": "none",
            "duration_minutes": 0,
        }

    location = "gym" if gym_access else ("home" if home_equipment else "outdoor")
    goal_label = {
        "muscle_gain": "hypertrophie",
        "weight_loss": "cardio / perte de graisse",
        "performance": "performance",
        "longevity": "endurance et mobilité",
        "maintenance": "entretien général",
    }.get(primary_goal or "maintenance", "entretien")

    recommendation = {
        "intensity": intensity,
        "location": location,
        "goal_focus": goal_label,
    }

    if intensity == "push":
        recommendation.update({
            "type": "strength" if primary_goal in ("muscle_gain", "performance") else "cardio",
            "duration_minutes": 60,
            "message": f"Excellente forme — séance intensive de {goal_label} recommandée.",
            "notes": "Volume élevé, progresser sur les exercices principaux.",
        })
    elif intensity == "normal":
        recommendation.update({
            "type": "mixed",
            "duration_minutes": 45,
            "message": f"Bonne récupération — séance standard de {goal_label}.",
            "notes": "Maintenir les charges habituelles.",
        })
    elif intensity == "moderate":
        recommendation.update({
            "type": "light_strength" if gym_access else "mobility",
            "duration_minutes": 30,
            "message": "Récupération modérée — séance légère ou mobilité recommandée.",
            "notes": "Réduire le volume de 20-30%. Écouter son corps.",
        })
    elif intensity == "light":
        recommendation.update({
            "type": "mobility",
            "duration_minutes": 20,
            "message": "Récupération insuffisante — mobilité ou marche uniquement.",
            "notes": "Pas de poids lourds. Étirements dynamiques, yoga léger.",
        })
    else:  # rest
        recommendation.update({
            "type": "rest",
            "duration_minutes": 0,
            "message": "Repos complet recommandé — récupération prioritaire.",
            "notes": "Sommeil, hydratation et nutrition au premier plan.",
        })

    return recommendation


def _build_daily_tips(
    readiness_level: str,
    hydration_pct: Optional[float],
    sleep_quality_label: Optional[str],
    protein_pct: Optional[float],
    calorie_pct: Optional[float],
    intermittent_fasting: bool = False,
    fasting_protocol: Optional[str] = None,
) -> List[str]:
    """Génère 2-4 conseils concrets prioritaires pour la journée."""
    tips: List[str] = []

    # Priorité 1 : récupération si mauvaise
    if readiness_level == "poor":
        tips.append("🛌 Récupération prioritaire aujourd'hui — coucher 1h plus tôt ce soir.")
    elif readiness_level == "fair" and sleep_quality_label in ("poor", "fair"):
        tips.append("😴 Sommeil insuffisant — éviter la caféine après 14h.")

    # Priorité 2 : hydratation si faible
    if hydration_pct is not None and hydration_pct < 0.60:
        tips.append("💧 Déshydratation détectée — commencer par 500ml d'eau maintenant.")
    elif hydration_pct is not None and hydration_pct < 0.80:
        tips.append("💧 Penser à s'hydrater régulièrement tout au long de la journée.")

    # Priorité 3 : protéines
    if protein_pct is not None and protein_pct < 0.60:
        tips.append("🥩 Protéines insuffisantes — inclure une source de protéine à chaque repas.")

    # Priorité 4 : déficit calorique excessif
    if calorie_pct is not None and calorie_pct < 0.70:
        tips.append("⚡ Apport énergétique bas — préparer des repas complets pour la journée.")

    # Conseil jeûne
    if intermittent_fasting and fasting_protocol:
        window = FASTING_WINDOW_HOURS.get(fasting_protocol, 8)
        tips.append(f"⏰ Jeûne {fasting_protocol} — fenêtre alimentaire de {window}h à respecter.")

    # Conseil général de bien-être (toujours présent si < 3 tips)
    if len(tips) < 2:
        tips.append("🌿 Profiter d'une journée équilibrée — activité, nutrition et récupération en harmonie.")

    return tips[:4]


def _build_eating_window(
    intermittent_fasting: bool,
    fasting_protocol: Optional[str],
    eating_window_hours: Optional[float],
    fasting_start_at: Optional[str],
    usual_wake_time: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Construit les informations de fenêtre alimentaire si jeûne actif."""
    if not intermittent_fasting or not fasting_protocol:
        return None

    window = {
        "protocol": fasting_protocol,
        "window_hours": eating_window_hours,
        "fasting_start": fasting_start_at,
    }

    if usual_wake_time:
        window["eating_start"] = str(usual_wake_time)[:5]

    return window


def _choose_nutrition_focus(
    avg_protein_pct: Optional[float],
    micro_score: Optional[float],
    top_deficiencies: Optional[list],
) -> Optional[str]:
    """Choisit un nutriment à surveiller particulièrement aujourd'hui."""
    if avg_protein_pct and avg_protein_pct < 0.70:
        return "Protéines — priorité haute aujourd'hui."
    if top_deficiencies and len(top_deficiencies) > 0:
        return f"Micronutriment à surveiller : {top_deficiencies[0]}."
    if micro_score and micro_score < 50:
        return "Variété alimentaire — augmenter la diversité des groupes d'aliments."
    return None


# ── Moteur principal ───────────────────────────────────────────────────────────

def generate_daily_health_plan(
    target_date_str: str,
    # Récupération
    readiness_score: Optional[float],
    recommended_intensity: str,
    # Nutrition
    nutrition_targets: NutritionTargets,
    # Profil
    primary_goal: Optional[str] = None,
    fitness_level: Optional[str] = None,
    home_equipment: Optional[list] = None,
    gym_access: bool = False,
    intermittent_fasting: bool = False,
    fasting_protocol: Optional[str] = None,
    usual_wake_time: Optional[str] = None,
    # État du jour
    has_workout_today: bool = False,
    hydration_pct: Optional[float] = None,     # ratio actuel / cible
    sleep_quality_label: Optional[str] = None,
    # Nutrition actuelle vs cible (ratios 0-1)
    protein_pct: Optional[float] = None,
    calorie_pct: Optional[float] = None,
    # Micronutriments
    micro_score: Optional[float] = None,
    top_deficiencies: Optional[list] = None,
    # Alertes brutes (depuis dashboard)
    raw_alerts: Optional[List[Dict[str, str]]] = None,
) -> DailyHealthPlan:
    """Génère le plan santé journalier complet."""
    level = _readiness_level(readiness_score)

    workout = _build_workout_recommendation(
        intensity=recommended_intensity,
        has_workout_today=has_workout_today,
        primary_goal=primary_goal,
        fitness_level=fitness_level,
        home_equipment=home_equipment,
        gym_access=gym_access,
    )

    tips = _build_daily_tips(
        readiness_level=level,
        hydration_pct=hydration_pct,
        sleep_quality_label=sleep_quality_label,
        protein_pct=protein_pct,
        calorie_pct=calorie_pct,
        intermittent_fasting=intermittent_fasting,
        fasting_protocol=fasting_protocol,
    )

    eating_window = _build_eating_window(
        intermittent_fasting=intermittent_fasting,
        fasting_protocol=fasting_protocol,
        eating_window_hours=nutrition_targets.eating_window_hours,
        fasting_start_at=nutrition_targets.fasting_start_at,
        usual_wake_time=usual_wake_time,
    )

    nutrition_focus = _choose_nutrition_focus(protein_pct, micro_score, top_deficiencies)

    # Alertes : filtrage des 3 plus importantes
    alerts = raw_alerts[:3] if raw_alerts else []

    return DailyHealthPlan(
        date=target_date_str,
        generated_at=datetime.now(timezone.utc),
        workout_recommendation=workout,
        protein_target_g=nutrition_targets.protein_target_g,
        calorie_target=nutrition_targets.calories_target,
        hydration_target_ml=nutrition_targets.hydration_target_ml,
        steps_goal=STEPS_DAILY_GOAL,
        sleep_target_hours=SLEEP_TARGET_HOURS,
        readiness_level=level,
        recommended_intensity=recommended_intensity,
        alerts=alerts,
        daily_tips=tips,
        eating_window=eating_window,
        nutrition_focus=nutrition_focus,
    )

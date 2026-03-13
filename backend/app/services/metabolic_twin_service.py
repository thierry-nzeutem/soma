"""
Metabolic Twin Service — SOMA LOT 9.

Calcule un état physiologique simplifié (MetabolicState) à partir des
données disponibles dans la base, puis persiste le snapshot.

Architecture :
  compute_metabolic_state()  → pure calculation → MetabolicState dataclass
  save_metabolic_state()     → DB persistence   → MetabolicStateSnapshot ORM
  get_or_compute_metabolic_state() → façade utilisée par context_builder

Contrainte : Le LLM ne réalise AUCUN calcul. Ce service est la seule source
de vérité pour les valeurs physiologiques.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.health import HydrationLog, SleepSession
from app.models.metrics import DailyMetrics
from app.models.nutrition import NutritionEntry
from app.models.scores import MetabolicStateSnapshot, ReadinessScore
from app.models.workout import WorkoutSession

logger = logging.getLogger(__name__)


# ── Résultat pur (pas de DB) ──────────────────────────────────────────────────

@dataclass
class MetabolicState:
    """État métabolique calculé — représentation pure, non persistée."""

    # Bilan énergétique
    energy_balance_kcal: Optional[float] = None      # intake - dépense
    estimated_bmr_kcal: Optional[float] = None
    estimated_tdee_kcal: Optional[float] = None
    energy_availability_kcal: Optional[float] = None  # tdee - exercice

    # Glycogène
    estimated_glycogen_g: Optional[float] = None
    glycogen_status: str = "unknown"  # depleted | low | normal | high

    # Fatigue & récupération
    fatigue_score: Optional[float] = None        # 0-100 (100 = très fatigué)
    recovery_score: Optional[float] = None       # 0-100 (100 = parfaitement récupéré)
    training_readiness: Optional[float] = None   # 0-100

    # Charge entraînement
    training_load_7d: Optional[float] = None
    training_load_28d: Optional[float] = None

    # Statuts nutritionnels
    protein_status: str = "unknown"       # insufficient | adequate | optimal | excess
    hydration_status: str = "unknown"     # dehydrated | low | normal | optimal

    # Signaux globaux
    stress_load: Optional[float] = None   # 0-100
    plateau_risk: bool = False
    metabolic_age: Optional[float] = None

    # Méta
    confidence_score: float = 0.0
    variables_used: list = field(default_factory=list)
    snapshot_date: Optional[date] = None


# ── Helpers de calcul purs ────────────────────────────────────────────────────

def _estimate_bmr(weight_kg: Optional[float], height_cm: Optional[float],
                  age: Optional[int], sex: Optional[str]) -> Optional[float]:
    """Harris-Benedict révisée (Mifflin-St Jeor)."""
    if not all([weight_kg, height_cm, age]):
        return None
    if sex == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def _estimate_tdee(bmr: Optional[float], activity_level: Optional[str]) -> Optional[float]:
    """TDEE = BMR × facteur d'activité."""
    if bmr is None:
        return None
    factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    factor = factors.get(activity_level or "moderate", 1.55)
    return bmr * factor


def _estimate_glycogen(
    carbs_g: Optional[float],
    training_load_7d: Optional[float],
    weight_kg: Optional[float],
) -> tuple[Optional[float], str]:
    """
    Estimation simplifiée du glycogène musculaire + hépatique.

    Stockage max ≈ 15 g/kg masse corporelle (muscles + foie).
    Réduction selon la charge d'entraînement des 7 derniers jours.
    """
    if weight_kg is None or weight_kg <= 0:
        return None, "unknown"

    max_glycogen = weight_kg * 15.0
    carb_contribution = min((carbs_g or 0) * 0.9, max_glycogen)
    depletion_factor = min((training_load_7d or 0) / 500.0, 0.8)
    estimated = max(0.0, carb_contribution * (1.0 - depletion_factor * 0.4))

    pct = estimated / max_glycogen if max_glycogen > 0 else 0
    if pct < 0.25:
        status = "depleted"
    elif pct < 0.50:
        status = "low"
    elif pct < 0.80:
        status = "normal"
    else:
        status = "high"
    return estimated, status


def _compute_fatigue(
    training_load_7d: Optional[float],
    sleep_score: Optional[float],
    hrv_ms: Optional[float],
    resting_hr: Optional[float],
) -> Optional[float]:
    """
    Fatigue 0-100 (100 = épuisé).
    Combine charge d'entraînement, qualité sommeil, HRV et FC repos.
    """
    components: list[float] = []

    if training_load_7d is not None:
        # Charge élevée → plus de fatigue (normalisé sur 400 = limite haute)
        components.append(min(training_load_7d / 400.0, 1.0) * 40)

    if sleep_score is not None:
        # Mauvais sommeil → plus de fatigue (sleep_score 0-100, inversé)
        components.append((1.0 - sleep_score / 100.0) * 35)

    if hrv_ms is not None:
        # HRV faible → plus de fatigue (normalisé sur 100 ms)
        components.append((1.0 - min(hrv_ms / 100.0, 1.0)) * 15)

    if resting_hr is not None:
        # FC repos élevée → plus de fatigue (normalisé : 100 bpm = max)
        components.append(min(resting_hr / 100.0, 1.0) * 10)

    if not components:
        return None
    return round(sum(components), 1)


def _compute_protein_status(
    protein_g: Optional[float],
    weight_kg: Optional[float],
    primary_goal: Optional[str],
) -> str:
    """Statut protéique basé sur les apports vs besoin estimé."""
    if protein_g is None or weight_kg is None or weight_kg <= 0:
        return "unknown"
    # Besoin min selon objectif
    need_per_kg = 1.6 if primary_goal in ("muscle_gain", "performance") else 1.2
    need = weight_kg * need_per_kg
    ratio = protein_g / need if need > 0 else 0
    if ratio < 0.6:
        return "insufficient"
    elif ratio < 0.9:
        return "adequate"
    elif ratio <= 1.5:
        return "optimal"
    return "excess"


def _compute_hydration_status(
    hydration_ml: Optional[float],
    hydration_target_ml: Optional[float],
) -> str:
    if hydration_ml is None or hydration_target_ml is None or hydration_target_ml <= 0:
        return "unknown"
    ratio = hydration_ml / hydration_target_ml
    if ratio < 0.50:
        return "dehydrated"
    elif ratio < 0.75:
        return "low"
    elif ratio < 1.05:
        return "normal"
    return "optimal"


def _compute_stress_load(
    fatigue_score: Optional[float],
    sleep_score: Optional[float],
    calorie_deficit: Optional[float],
) -> Optional[float]:
    """Charge de stress globale 0-100."""
    parts: list[float] = []
    if fatigue_score is not None:
        parts.append(fatigue_score * 0.5)
    if sleep_score is not None:
        parts.append((1.0 - sleep_score / 100.0) * 30)
    if calorie_deficit is not None and calorie_deficit < 0:
        # Déficit sévère > 800 kcal → stress nutritionnel
        parts.append(min(abs(calorie_deficit) / 800.0, 1.0) * 20)
    if not parts:
        return None
    return round(min(sum(parts), 100.0), 1)


def _estimate_metabolic_age(
    longevity_score: Optional[float],
    actual_age: Optional[int],
) -> Optional[float]:
    """
    Estimation grossière de l'âge métabolique.
    Score longévité 100 → âge métab = âge réel - 10 ans
    Score longévité 50  → âge métab = âge réel
    Score longévité 0   → âge métab = âge réel + 15 ans
    """
    if actual_age is None or longevity_score is None:
        return None
    delta = (longevity_score - 50) / 50.0 * 10
    return round(max(18.0, actual_age - delta), 1)


def _detect_plateau(
    weights: list[float],
    calories_list: list[float],
) -> bool:
    """
    Détecte un plateau si sur 14 jours :
    - l'écart-type du poids < 0.5 kg (stable)
    - les calories sont relativement constantes (écart-type < 200 kcal)
    """
    if len(weights) < 10 or len(calories_list) < 10:
        return False
    import statistics
    try:
        weight_std = statistics.stdev(weights)
        cal_std = statistics.stdev(calories_list)
        return weight_std < 0.5 and cal_std < 200
    except statistics.StatisticsError:
        return False


# ── Calcul pur ────────────────────────────────────────────────────────────────

def compute_metabolic_state(
    *,
    metrics: Optional[DailyMetrics],
    readiness: Optional[ReadinessScore],
    weight_kg: Optional[float],
    height_cm: Optional[float],
    age: Optional[int],
    sex: Optional[str],
    activity_level: Optional[str],
    primary_goal: Optional[str],
    longevity_score: Optional[float],
    recent_weights: Optional[list[float]] = None,
    recent_calories: Optional[list[float]] = None,
    target_date: Optional[date] = None,
) -> MetabolicState:
    """
    Calcul pur de MetabolicState — aucune lecture DB.
    Toutes les entrées sont passées en argument.
    """
    state = MetabolicState(snapshot_date=target_date or date.today())
    variables_used: list[str] = []

    # ── BMR / TDEE ──────────────────────────────────────────────────────────
    bmr = _estimate_bmr(weight_kg, height_cm, age, sex)
    tdee = _estimate_tdee(bmr, activity_level)
    state.estimated_bmr_kcal = round(bmr, 1) if bmr else None
    state.estimated_tdee_kcal = round(tdee, 1) if tdee else None
    if bmr:
        variables_used += ["weight_kg", "height_cm", "age", "sex", "activity_level"]

    # ── Bilan énergétique ──────────────────────────────────────────────────
    calories_in = getattr(metrics, "calories_consumed", None)
    if calories_in is not None and tdee is not None:
        state.energy_balance_kcal = round(calories_in - tdee, 1)
        variables_used.append("calories_consumed")

    training_load = getattr(metrics, "training_load", None) or 0.0
    state.training_load_7d = training_load
    if training_load:
        variables_used.append("training_load")

    active_cal = getattr(metrics, "active_calories_kcal", None) or 0.0
    if tdee is not None:
        state.energy_availability_kcal = round(tdee - active_cal, 1)

    # ── Glycogène ──────────────────────────────────────────────────────────
    carbs_g = getattr(metrics, "carbs_g", None)
    gly_g, gly_status = _estimate_glycogen(carbs_g, training_load, weight_kg)
    state.estimated_glycogen_g = round(gly_g, 1) if gly_g is not None else None
    state.glycogen_status = gly_status
    if carbs_g is not None:
        variables_used.append("carbs_g")

    # ── Fatigue ────────────────────────────────────────────────────────────
    sleep_score = getattr(metrics, "sleep_score", None)
    hrv_ms = getattr(metrics, "hrv_ms", None)
    rhr = getattr(metrics, "resting_heart_rate_bpm", None)
    fatigue = _compute_fatigue(training_load, sleep_score, hrv_ms, rhr)
    state.fatigue_score = fatigue
    if sleep_score is not None:
        variables_used.append("sleep_score")
    if hrv_ms is not None:
        variables_used.append("hrv_ms")

    # ── Récupération ───────────────────────────────────────────────────────
    if readiness:
        state.recovery_score = readiness.recovery_score
        state.training_readiness = readiness.overall_readiness
        variables_used.append("readiness_score")

    # ── Statuts nutritionnels ──────────────────────────────────────────────
    protein_g = getattr(metrics, "protein_g", None)
    state.protein_status = _compute_protein_status(protein_g, weight_kg, primary_goal)
    if protein_g is not None:
        variables_used.append("protein_g")

    hydration_ml = getattr(metrics, "hydration_ml", None)
    hydration_target = getattr(metrics, "hydration_target_ml", None)
    state.hydration_status = _compute_hydration_status(hydration_ml, hydration_target)
    if hydration_ml is not None:
        variables_used.append("hydration_ml")

    # ── Stress global ──────────────────────────────────────────────────────
    state.stress_load = _compute_stress_load(
        fatigue,
        sleep_score,
        state.energy_balance_kcal,
    )

    # ── Plateau ────────────────────────────────────────────────────────────
    state.plateau_risk = _detect_plateau(
        recent_weights or [],
        recent_calories or [],
    )

    # ── Âge métabolique ────────────────────────────────────────────────────
    state.metabolic_age = _estimate_metabolic_age(longevity_score, age)
    if longevity_score is not None:
        variables_used.append("longevity_score")

    # ── Confiance ──────────────────────────────────────────────────────────
    # Proportionnelle au nb de variables disponibles (max 12)
    state.confidence_score = round(min(len(variables_used) / 12.0, 1.0), 2)
    state.variables_used = variables_used

    return state


# ── Persistence DB ────────────────────────────────────────────────────────────

async def save_metabolic_state(
    db: AsyncSession,
    user_id: uuid.UUID,
    state: MetabolicState,
) -> MetabolicStateSnapshot:
    """Upsert du MetabolicState dans la table metabolic_state_snapshots."""
    target_date = state.snapshot_date or date.today()

    result = await db.execute(
        select(MetabolicStateSnapshot).where(
            and_(
                MetabolicStateSnapshot.user_id == user_id,
                MetabolicStateSnapshot.snapshot_date == target_date,
            )
        )
    )
    snap = result.scalar_one_or_none()

    if snap is None:
        snap = MetabolicStateSnapshot(user_id=user_id, snapshot_date=target_date)
        db.add(snap)

    # Champs existants
    snap.estimated_bmr_kcal = state.estimated_bmr_kcal
    snap.estimated_tdee_kcal = state.estimated_tdee_kcal
    snap.estimated_glycogen_g = state.estimated_glycogen_g
    snap.glycogen_status = state.glycogen_status
    snap.fatigue_score = state.fatigue_score
    snap.recovery_score = state.recovery_score
    snap.readiness_score = state.training_readiness
    snap.training_load_7d = state.training_load_7d
    snap.energy_availability_kcal = state.energy_availability_kcal
    snap.confidence_score = state.confidence_score
    snap.variables_used = state.variables_used

    # Nouveaux champs (V006)
    snap.protein_status = state.protein_status
    snap.hydration_status = state.hydration_status
    snap.stress_load = state.stress_load
    snap.plateau_risk = state.plateau_risk
    snap.metabolic_age = state.metabolic_age

    await db.flush()
    logger.info("MetabolicState sauvegardé pour user %s date %s (confiance %.0f%%)",
                user_id, target_date, state.confidence_score * 100)
    return snap


async def get_or_compute_metabolic_state(
    db: AsyncSession,
    user_id: uuid.UUID,
    profile,
    target_date: Optional[date] = None,
) -> MetabolicState:
    """
    Façade : récupère le snapshot du jour ou le calcule + le sauvegarde.

    Utilisée par context_builder pour éviter les recalculs répétés.
    """
    target_date = target_date or date.today()

    # ── Métriques du jour ──────────────────────────────────────────────────
    metrics_res = await db.execute(
        select(DailyMetrics).where(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.metrics_date == target_date,
            )
        )
    )
    metrics = metrics_res.scalar_one_or_none()

    # ── Readiness ─────────────────────────────────────────────────────────
    readiness_res = await db.execute(
        select(ReadinessScore).where(
            and_(
                ReadinessScore.user_id == user_id,
                ReadinessScore.score_date == target_date,
            )
        )
    )
    readiness = readiness_res.scalar_one_or_none()

    # ── Historique récent (14 jours) pour plateau ─────────────────────────
    since_14 = target_date - timedelta(days=14)
    hist_res = await db.execute(
        select(DailyMetrics).where(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.metrics_date >= since_14,
                DailyMetrics.metrics_date <= target_date,
            )
        ).order_by(DailyMetrics.metrics_date)
    )
    history = hist_res.scalars().all()
    recent_weights = [h.weight_kg for h in history if h.weight_kg]
    recent_calories = [h.calories_consumed for h in history if h.calories_consumed]

    # ── Longevity (dernier disponible) ────────────────────────────────────
    from app.models.scores import LongevityScore
    lon_res = await db.execute(
        select(LongevityScore)
        .where(LongevityScore.user_id == user_id)
        .order_by(LongevityScore.score_date.desc())
        .limit(1)
    )
    lon = lon_res.scalar_one_or_none()

    # ── Calcul ────────────────────────────────────────────────────────────
    weight_kg = getattr(metrics, "weight_kg", None)
    state = compute_metabolic_state(
        metrics=metrics,
        readiness=readiness,
        weight_kg=weight_kg or (profile.weight_kg if profile else None),
        height_cm=profile.height_cm if profile else None,
        age=profile.age if profile else None,
        sex=profile.sex if profile else None,
        activity_level=profile.activity_level if profile else None,
        primary_goal=profile.primary_goal if profile else None,
        longevity_score=lon.longevity_score if lon else None,
        recent_weights=recent_weights,
        recent_calories=recent_calories,
        target_date=target_date,
    )

    await save_metabolic_state(db, user_id, state)
    return state

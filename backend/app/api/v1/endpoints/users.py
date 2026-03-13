from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import numpy as np

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserProfile, BodyMetric
from app.schemas.user import ProfileUpdate, ProfileResponse, BodyMetricCreate, BodyMetricResponse, BodyMetricsTrend, ComputedMetrics
from app.services.calculations import (
    calculate_bmr_mifflin, calculate_bmr_katch_mcardle, calculate_tdee,
    calculate_bmi, calculate_calorie_target, calculate_protein_target,
    calculate_hydration_target, calculate_profile_completeness,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


def _compute_metrics(profile: UserProfile, latest_weight: Optional[float] = None) -> Optional[ComputedMetrics]:
    """Recalcule toutes les métriques physiologiques depuis le profil."""
    weight = latest_weight or getattr(profile, '_latest_weight', None)
    if not weight or not profile.height_cm or not profile.age or not profile.sex:
        return None

    bmi = calculate_bmi(weight, profile.height_cm)
    bmr = calculate_bmr_mifflin(weight, profile.height_cm, profile.age, profile.sex)
    tdee = calculate_tdee(bmr, profile.activity_level or "moderate")

    target_cal, _ = calculate_calorie_target(
        tdee, profile.primary_goal or "maintenance", weight, profile.goal_weight_kg
    )

    protein_min, protein_max, _ = calculate_protein_target(
        weight, profile.primary_goal or "maintenance", profile.fitness_level or "beginner"
    )

    hydration, _ = calculate_hydration_target(weight, profile.activity_level or "moderate")

    return ComputedMetrics(
        bmi=round(bmi, 1),
        bmr_kcal=round(bmr, 0),
        tdee_kcal=round(tdee, 0),
        target_calories_kcal=target_cal,
        target_protein_g=round((protein_min + protein_max) / 2, 0),
        protein_min_g=protein_min,
        protein_max_g=protein_max,
        target_hydration_ml=hydration,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Récupérer le dernier poids
    weight_result = await db.execute(
        select(BodyMetric.weight_kg)
        .where(BodyMetric.user_id == current_user.id, BodyMetric.weight_kg.isnot(None))
        .order_by(BodyMetric.measured_at.desc())
        .limit(1)
    )
    latest_weight = weight_result.scalar_one_or_none()

    computed = _compute_metrics(profile, latest_weight)

    # Calculer complétude
    profile_dict = {
        "age": profile.age, "sex": profile.sex, "height_cm": profile.height_cm,
        "primary_goal": profile.primary_goal, "activity_level": profile.activity_level,
        "fitness_level": profile.fitness_level, "dietary_regime": profile.dietary_regime,
        "intermittent_fasting": profile.intermittent_fasting, "meals_per_day": profile.meals_per_day,
        "preferred_training_time": profile.preferred_training_time,
        "food_allergies": profile.food_allergies, "home_equipment": profile.home_equipment,
        "gym_access": profile.gym_access, "avg_energy_level": profile.avg_energy_level,
        "perceived_sleep_quality": profile.perceived_sleep_quality,
        "physical_constraints": profile.physical_constraints,
    }
    completeness = calculate_profile_completeness(profile_dict)

    return ProfileResponse(
        id=profile.id,
        first_name=profile.first_name,
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        goal_weight_kg=profile.goal_weight_kg,
        primary_goal=profile.primary_goal,
        activity_level=profile.activity_level,
        fitness_level=profile.fitness_level,
        dietary_regime=profile.dietary_regime,
        intermittent_fasting=profile.intermittent_fasting,
        fasting_protocol=profile.fasting_protocol,
        meals_per_day=profile.meals_per_day,
        home_equipment=profile.home_equipment,
        gym_access=profile.gym_access,
        avg_energy_level=profile.avg_energy_level,
        perceived_sleep_quality=profile.perceived_sleep_quality,
        computed=computed,
        profile_completeness_score=completeness,
        theme_preference=profile.theme_preference,
        locale=profile.locale,
        timezone=profile.timezone,
    )


@router.put("", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Mise à jour des champs fournis
    update_data = data.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)

    # Re-calculer métriques
    weight_result = await db.execute(
        select(BodyMetric.weight_kg)
        .where(BodyMetric.user_id == current_user.id, BodyMetric.weight_kg.isnot(None))
        .order_by(BodyMetric.measured_at.desc())
        .limit(1)
    )
    latest_weight = weight_result.scalar_one_or_none()
    computed = _compute_metrics(profile, latest_weight)

    profile_dict = data.model_dump()
    completeness = calculate_profile_completeness(profile_dict)

    return ProfileResponse(
        id=profile.id,
        first_name=profile.first_name,
        age=profile.age,
        sex=profile.sex,
        height_cm=profile.height_cm,
        goal_weight_kg=profile.goal_weight_kg,
        primary_goal=profile.primary_goal,
        activity_level=profile.activity_level,
        fitness_level=profile.fitness_level,
        dietary_regime=profile.dietary_regime,
        intermittent_fasting=profile.intermittent_fasting,
        fasting_protocol=profile.fasting_protocol,
        meals_per_day=profile.meals_per_day,
        home_equipment=profile.home_equipment,
        gym_access=profile.gym_access,
        avg_energy_level=profile.avg_energy_level,
        perceived_sleep_quality=profile.perceived_sleep_quality,
        computed=computed,
        profile_completeness_score=completeness,
        theme_preference=profile.theme_preference,
        locale=profile.locale,
        timezone=profile.timezone,
    )


# --- Body metrics ---

body_router = APIRouter(prefix="/body-metrics", tags=["Body Metrics"])


@body_router.post("", response_model=BodyMetricResponse, status_code=201)
async def add_body_metric(
    data: BodyMetricCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    metric = BodyMetric(
        user_id=current_user.id,
        measured_at=data.measured_at or datetime.now(timezone.utc),
        weight_kg=data.weight_kg,
        body_fat_pct=data.body_fat_pct,
        muscle_mass_kg=data.muscle_mass_kg,
        bone_mass_kg=data.bone_mass_kg,
        visceral_fat_index=data.visceral_fat_index,
        water_pct=data.water_pct,
        metabolic_age=data.metabolic_age,
        trunk_fat_pct=data.trunk_fat_pct,
        trunk_muscle_pct=data.trunk_muscle_pct,
        waist_cm=data.waist_cm,
        notes=data.notes,
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return metric


@body_router.get("", response_model=BodyMetricsTrend)
async def get_body_metrics(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import timedelta

    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(BodyMetric)
        .where(BodyMetric.user_id == current_user.id, BodyMetric.measured_at >= since)
        .order_by(BodyMetric.measured_at.desc())
    )
    entries = result.scalars().all()

    # Calcul tendance poids
    trend = None
    weights = [(e.measured_at.timestamp(), e.weight_kg) for e in entries if e.weight_kg]
    if len(weights) >= 3:
        timestamps, values = zip(*weights)
        # Régression linéaire simple
        t = np.array(timestamps)
        w = np.array(values)
        t_centered = t - t.mean()
        slope = float(np.sum(t_centered * w) / np.sum(t_centered ** 2))
        # Convertir en kg/semaine
        slope_per_week = slope * 7 * 86400
        trend = {
            "weight_slope_kg_per_week": round(slope_per_week, 3),
            "direction": "decreasing" if slope_per_week < -0.05 else ("increasing" if slope_per_week > 0.05 else "stable"),
        }

    # BMI actuel
    latest = next((e for e in entries if e.weight_kg), None)
    current_bmi = None
    if latest:
        profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))
        profile = profile_result.scalar_one_or_none()
        if profile and profile.height_cm:
            current_bmi = round(calculate_bmi(latest.weight_kg, profile.height_cm), 1)

    return BodyMetricsTrend(entries=list(entries), trend=trend, current_bmi=current_bmi)

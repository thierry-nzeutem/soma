from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserProfile
from app.models.health import HealthSample

fitness_router = APIRouter(prefix="/fitness", tags=["Cardio Fitness"])

# Tables de reference VO2max (ml/kg/min) par age et sexe
# Source: Cooper Institute / ACSM norms
# Format: {age_group: {percentile: value}} pour homme et femme
VO2MAX_NORMS_MALE = {
    (20, 29): {1: 31, 10: 38, 25: 42, 50: 48, 75: 52, 90: 56, 99: 62},
    (30, 39): {1: 29, 10: 35, 25: 39, 50: 45, 75: 49, 90: 53, 99: 59},
    (40, 49): {1: 26, 10: 32, 25: 36, 50: 42, 75: 46, 90: 51, 99: 57},
    (50, 59): {1: 22, 10: 28, 25: 33, 50: 39, 75: 43, 90: 47, 99: 53},
    (60, 69): {1: 20, 10: 24, 25: 28, 50: 34, 75: 38, 90: 42, 99: 48},
    (70, 99): {1: 17, 10: 21, 25: 24, 50: 29, 75: 33, 90: 37, 99: 43},
}
VO2MAX_NORMS_FEMALE = {
    (20, 29): {1: 24, 10: 30, 25: 34, 50: 39, 75: 43, 90: 47, 99: 53},
    (30, 39): {1: 22, 10: 28, 25: 32, 50: 37, 75: 41, 90: 45, 99: 51},
    (40, 49): {1: 19, 10: 25, 25: 29, 50: 34, 75: 38, 90: 42, 99: 48},
    (50, 59): {1: 18, 10: 22, 25: 26, 50: 30, 75: 34, 90: 38, 99: 44},
    (60, 69): {1: 16, 10: 19, 25: 23, 50: 27, 75: 31, 90: 34, 99: 40},
    (70, 99): {1: 14, 10: 17, 25: 20, 50: 24, 75: 28, 90: 31, 99: 37},
}

VO2MAX_CATEGORIES = [
    (0, 25, "Tres faible"),
    (25, 35, "Faible"),
    (35, 42, "Moyen"),
    (42, 50, "Bon"),
    (50, 58, "Tres bon"),
    (58, 999, "Excellent"),
]

def _get_norms(age: int, sex: str) -> dict:
    norms = VO2MAX_NORMS_MALE if sex == "male" else VO2MAX_NORMS_FEMALE
    for (lo, hi), v in norms.items():
        if lo <= age <= hi:
            return v
    return list(norms.values())[-1]

def _percentile(vo2: float, age: int, sex: str) -> int:
    norms = _get_norms(age, sex)
    if vo2 >= norms[99]: return 99
    if vo2 <= norms[1]: return 1
    percs = sorted(norms.keys())
    for i in range(len(percs) - 1):
        lo, hi = percs[i], percs[i + 1]
        if norms[lo] <= vo2 < norms[hi]:
            frac = (vo2 - norms[lo]) / (norms[hi] - norms[lo])
            return int(lo + frac * (hi - lo))
    return 50

def _category(vo2: float) -> str:
    for lo, hi, label in VO2MAX_CATEGORIES:
        if lo <= vo2 < hi:
            return label
    return "Excellent"

def _reference_bar(age_ref: int, sex: str) -> dict:
    norms = _get_norms(age_ref, sex)
    return {"p25": norms[25], "p50": norms[50], "p75": norms[75], "age": age_ref}

class CardioFitnessResponse(BaseModel):
    measured_at: Optional[datetime] = None
    vo2max: Optional[float] = None
    category: Optional[str] = None
    percentile: Optional[int] = None
    reference_ages: List[dict] = []
    improvement_suggestion: Optional[str] = None
    note: Optional[str] = None

class CardioHistoryEntry(BaseModel):
    measured_at: datetime
    vo2max: float
    percentile: Optional[int] = None

class CardioHistoryResponse(BaseModel):
    total: int
    entries: List[CardioHistoryEntry]

@fitness_router.get("/cardio-fitness", response_model=CardioFitnessResponse)
async def get_cardio_fitness(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    result = await db.execute(
        select(HealthSample)
        .where(HealthSample.user_id == current_user.id, HealthSample.sample_type == "vo2_max")
        .order_by(HealthSample.recorded_at.desc())
        .limit(1)
    )
    sample = result.scalar_one_or_none()
    if not sample:
        return CardioFitnessResponse()
    vo2 = sample.value
    age = profile.age if profile else 35
    sex = profile.sex if profile else "male"
    perc = _percentile(vo2, age, sex)
    cat = _category(vo2)
    refs = []
    for ref_age in [25, 35, 45, 55]:
        if abs(ref_age - age) <= 15:
            refs.append(_reference_bar(ref_age, sex))
    if perc < 25:
        sug = "Pratiquez 3 seances cardio par semaine pendant 2-3 mois pour ameliorer votre score de 10%."
    elif perc < 50:
        sug = "Augmentez progressivement vos seances d activite moderee a intense."
    else:
        sug = "Maintenez votre niveau avec des seances regulieres. Excellent travail !"
    return CardioFitnessResponse(
        measured_at=sample.recorded_at,
        vo2max=round(vo2, 1),
        category=cat,
        percentile=perc,
        reference_ages=refs,
        improvement_suggestion=sug,
    )

@fitness_router.get("/cardio-fitness/history", response_model=CardioHistoryResponse)
async def get_cardio_fitness_history(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    age = profile.age if profile else 35
    sex = profile.sex if profile else "male"
    total = (await db.execute(
        select(sqlfunc.count()).select_from(HealthSample)
        .where(HealthSample.user_id == current_user.id, HealthSample.sample_type == "vo2_max")
    )).scalar_one()
    result = await db.execute(
        select(HealthSample)
        .where(HealthSample.user_id == current_user.id, HealthSample.sample_type == "vo2_max")
        .order_by(HealthSample.recorded_at.desc()).limit(limit)
    )
    entries = [
        CardioHistoryEntry(measured_at=s.recorded_at, vo2max=round(s.value, 1), percentile=_percentile(s.value, age, sex))
        for s in result.scalars().all()
    ]
    return CardioHistoryResponse(total=total, entries=entries)

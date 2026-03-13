from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc
from pydantic import BaseModel
import uuid
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserProfile, BodyMetric
from app.services.calculations import calculate_bmi, calculate_bmr_mifflin

body_composition_router = APIRouter(prefix="/body", tags=["Body Composition"])
PERIOD_DAYS = {"week": 7, "month": 30, "quarter": 90, "semester": 180, "year": 365}

class CompositionPoint(BaseModel):
    date: str
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    visceral_fat_index: Optional[float] = None
    water_pct: Optional[float] = None
    metabolic_age: Optional[int] = None
    trunk_fat_pct: Optional[float] = None
    trunk_muscle_pct: Optional[float] = None

class SegmentationTrend(BaseModel):
    label: str
    current_value: Optional[float] = None
    delta: Optional[float] = None
    direction: str = "stable"

class CompositionTrendResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    measurements: int
    data_points: List[CompositionPoint]
    latest: Optional[CompositionPoint] = None
    segmentation: List[SegmentationTrend] = []
    weight_delta_kg: Optional[float] = None
    fat_delta_pct: Optional[float] = None
    muscle_delta_kg: Optional[float] = None

class AllDataEntry(BaseModel):
    id: uuid.UUID
    measured_at: datetime
    weight_kg: Optional[float] = None
    body_fat_pct: Optional[float] = None
    muscle_mass_kg: Optional[float] = None
    bone_mass_kg: Optional[float] = None
    visceral_fat_index: Optional[float] = None
    water_pct: Optional[float] = None
    metabolic_age: Optional[int] = None
    notes: Optional[str] = None
    source: str
    class Config:
        from_attributes = True

class AllDataResponse(BaseModel):
    total: int
    limit: int
    offset: int
    entries: List[AllDataEntry]

class WeightPoint(BaseModel):
    date: str
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    bmr_kcal: Optional[float] = None

class WeightTrendDetail(BaseModel):
    label: str
    delta_kg: float
    delta_pct: float

class WeightTrendResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    measurements: int
    data_points: List[WeightPoint]
    latest_weight_kg: Optional[float] = None
    latest_bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    latest_bmr_kcal: Optional[float] = None
    metabolic_age: Optional[int] = None
    trend: Optional[WeightTrendDetail] = None

def _bmi_category(bmi):
    if bmi < 18.5: return "Insuffisance ponderale"
    if bmi < 25.0: return "Poids normal"
    if bmi < 30.0: return "Surpoids"
    if bmi < 35.0: return "Obesite moderee"
    return "Obesite severe"

def _dir(delta, threshold=0.1):
    if delta is None: return "stable"
    return "up" if delta > threshold else ("down" if delta < -threshold else "stable")

@body_composition_router.get("/composition/trend", response_model=CompositionTrendResponse)
async def get_composition_trend(
    period: str = Query("month", pattern="^(week|month|quarter|semester|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    days = PERIOD_DAYS[period]
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    result = await db.execute(
        select(BodyMetric).where(BodyMetric.user_id == current_user.id, BodyMetric.measured_at >= since)
        .order_by(BodyMetric.measured_at.asc())
    )
    entries = result.scalars().all()
    pts = [CompositionPoint(
        date=e.measured_at.strftime("%Y-%m-%d"), weight_kg=e.weight_kg, body_fat_pct=e.body_fat_pct,
        muscle_mass_kg=e.muscle_mass_kg, bone_mass_kg=e.bone_mass_kg, visceral_fat_index=e.visceral_fat_index,
        water_pct=e.water_pct, metabolic_age=e.metabolic_age, trunk_fat_pct=e.trunk_fat_pct,
        trunk_muscle_pct=e.trunk_muscle_pct,
    ) for e in entries]
    latest = pts[-1] if pts else None
    first = pts[0] if pts else None
    wd = fd = md = None
    if first and latest:
        if first.weight_kg and latest.weight_kg: wd = round(latest.weight_kg - first.weight_kg, 2)
        if first.body_fat_pct and latest.body_fat_pct: fd = round(latest.body_fat_pct - first.body_fat_pct, 2)
        if first.muscle_mass_kg and latest.muscle_mass_kg: md = round(latest.muscle_mass_kg - first.muscle_mass_kg, 2)
    seg = []
    if latest:
        if latest.body_fat_pct is not None:
            seg.append(SegmentationTrend(label="Graisse corporelle", current_value=latest.body_fat_pct, delta=fd, direction=_dir(fd)))
        if latest.muscle_mass_kg and latest.weight_kg:
            mpct = round(latest.muscle_mass_kg / latest.weight_kg * 100, 1)
            fpct = round(first.muscle_mass_kg / first.weight_kg * 100, 1) if first and first.muscle_mass_kg and first.weight_kg else None
            dpct = round(mpct - fpct, 2) if fpct is not None else None
            seg.append(SegmentationTrend(label="Masse musculaire", current_value=mpct, delta=dpct, direction=_dir(dpct)))
        if latest.trunk_fat_pct is not None:
            td = round(latest.trunk_fat_pct - first.trunk_fat_pct, 2) if first and first.trunk_fat_pct else None
            seg.append(SegmentationTrend(label="Graisse tronc", current_value=latest.trunk_fat_pct, delta=td, direction=_dir(td)))
        if latest.bone_mass_kg is not None:
            bd = round(latest.bone_mass_kg - first.bone_mass_kg, 3) if first and first.bone_mass_kg else None
            seg.append(SegmentationTrend(label="Masse osseuse", current_value=latest.bone_mass_kg, delta=bd, direction="stable"))
        if latest.visceral_fat_index is not None:
            vd = round(latest.visceral_fat_index - first.visceral_fat_index, 1) if first and first.visceral_fat_index else None
            seg.append(SegmentationTrend(label="Graisse viscerale", current_value=latest.visceral_fat_index, delta=vd, direction=_dir(vd, 0.5)))
        if latest.water_pct is not None:
            wd2 = round(latest.water_pct - first.water_pct, 2) if first and first.water_pct else None
            seg.append(SegmentationTrend(label="Eau corporelle", current_value=latest.water_pct, delta=wd2, direction=_dir(wd2)))
    return CompositionTrendResponse(period=period, start_date=since.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"), measurements=len(entries), data_points=pts,
        latest=latest, segmentation=seg, weight_delta_kg=wd, fat_delta_pct=fd, muscle_delta_kg=md)

@body_composition_router.get("/composition/all-data", response_model=AllDataResponse)
async def get_all_body_data(
    limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    total = (await db.execute(
        select(sqlfunc.count()).select_from(BodyMetric).where(BodyMetric.user_id == current_user.id)
    )).scalar_one()
    result = await db.execute(
        select(BodyMetric).where(BodyMetric.user_id == current_user.id)
        .order_by(BodyMetric.measured_at.desc()).limit(limit).offset(offset)
    )
    return AllDataResponse(total=total, limit=limit, offset=offset,
        entries=[AllDataEntry.model_validate(e) for e in result.scalars().all()])

@body_composition_router.get("/weight/trend", response_model=WeightTrendResponse)
async def get_weight_trend(
    period: str = Query("month", pattern="^(week|month|quarter|semester|year)$"),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    days = PERIOD_DAYS[period]
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    profile = (await db.execute(select(UserProfile).where(UserProfile.user_id == current_user.id))).scalar_one_or_none()
    result = await db.execute(
        select(BodyMetric).where(
            BodyMetric.user_id == current_user.id, BodyMetric.measured_at >= since, BodyMetric.weight_kg.isnot(None),
        ).order_by(BodyMetric.measured_at.asc())
    )
    entries = result.scalars().all()
    pts = []
    for e in entries:
        bmi = bmr = None
        if profile and profile.height_cm:
            bmi = round(calculate_bmi(e.weight_kg, profile.height_cm), 1)
        if profile and profile.height_cm and profile.age and profile.sex:
            bmr = round(calculate_bmr_mifflin(e.weight_kg, profile.height_cm, profile.age, profile.sex), 0)
        pts.append(WeightPoint(date=e.measured_at.strftime("%Y-%m-%d %H:%M"), weight_kg=e.weight_kg, bmi=bmi, bmr_kcal=bmr))
    latest = entries[-1] if entries else None
    first = entries[0] if entries else None
    lb = bc = lbmr = lma = None
    if latest:
        if profile and profile.height_cm:
            lb = round(calculate_bmi(latest.weight_kg, profile.height_cm), 1)
            bc = _bmi_category(lb)
        if profile and profile.height_cm and profile.age and profile.sex:
            lbmr = round(calculate_bmr_mifflin(latest.weight_kg, profile.height_cm, profile.age, profile.sex), 0)
        lma = latest.metabolic_age
    trend = None
    if first and latest and abs(latest.weight_kg - first.weight_kg) > 0.01:
        delta = round(latest.weight_kg - first.weight_kg, 2)
        dpct = round(delta / first.weight_kg * 100, 1) if first.weight_kg else 0.0
        lbl = "Perte de poids" if delta < -0.2 else ("Prise de poids" if delta > 0.2 else "Stable")
        trend = WeightTrendDetail(label=lbl, delta_kg=delta, delta_pct=dpct)
    return WeightTrendResponse(period=period, start_date=since.strftime("%Y-%m-%d"),
        end_date=now.strftime("%Y-%m-%d"), measurements=len(entries), data_points=pts,
        latest_weight_kg=latest.weight_kg if latest else None,
        latest_bmi=lb, bmi_category=bc, latest_bmr_kcal=lbmr, metabolic_age=lma, trend=trend)

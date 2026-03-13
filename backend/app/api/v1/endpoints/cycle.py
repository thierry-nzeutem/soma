"""Suivi du cycle menstruel SOMA."""
from datetime import datetime, timezone, timedelta, date as date_type
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from pydantic import BaseModel
import uuid
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User

cycle_router = APIRouter(prefix="/cycle", tags=["Cycle Menstruel"])

PHASE_RECOMMENDATIONS = {
    "menstruation": {
        "label": "Menstruation",
        "duration_days": "1-5",
        "energy": "basse",
        "training": "Privilegiez yoga, marche douce, etirements. Evitez les efforts intenses.",
        "nutrition": "Augmentez fer (epinards, lentilles), omega-3 anti-inflammatoires, hydratation ++",
        "sleep": "Besoin de sommeil accru normal. Visez 8-9h.",
        "color": "EF4444",
    },
    "folliculaire": {
        "label": "Phase folliculaire",
        "duration_days": "6-13",
        "energy": "croissante",
        "training": "Ideale pour HIIT, musculation progressive, sports collectifs. Energie au maximum.",
        "nutrition": "Privilegiez proteines maigres, glucides complexes, aliments fermenentes.",
        "sleep": "Sommeil naturellement plus leger. 7-8h suffisent.",
        "color": "F59E0B",
    },
    "ovulation": {
        "label": "Ovulation",
        "duration_days": "14-16",
        "energy": "maximale",
        "training": "Performance maximale ! Testez vos records, entrainements d'intensite elevee.",
        "nutrition": "Antioxydants (baies, legumes colores), zinc, vitamine C pour le pic oestrogen.",
        "sleep": "Qualite de sommeil optimale. Energie pic.",
        "color": "10B981",
    },
    "luteale": {
        "label": "Phase luteale",
        "duration_days": "17-28",
        "energy": "decroissante",
        "training": "Cardio modere, pilates, natation. Reduisez les volumes. Ecoutez votre corps.",
        "nutrition": "Magnesium (chocolat noir, noix), vitamine B6, reduisez sel et sucres raffines.",
        "sleep": "Difficulte d'endormissement possible. Routine de sommeil stricte conseilee.",
        "color": "8B5CF6",
    },
}


def _current_phase(last_start: date_type, cycle_length: int = 28) -> dict:
    today = date_type.today()
    day_in_cycle = (today - last_start).days + 1
    day_in_cycle = ((day_in_cycle - 1) % cycle_length) + 1  # normalise dans le cycle

    if day_in_cycle <= 5:
        phase_key = "menstruation"
    elif day_in_cycle <= 13:
        phase_key = "folliculaire"
    elif day_in_cycle <= 16:
        phase_key = "ovulation"
    else:
        phase_key = "luteale"

    info = PHASE_RECOMMENDATIONS[phase_key].copy()
    next_period = last_start + timedelta(days=cycle_length)
    days_until_period = (next_period - today).days

    return {
        "phase_key": phase_key,
        "phase_label": info["label"],
        "day_in_cycle": day_in_cycle,
        "cycle_length": cycle_length,
        "days_until_next_period": max(0, days_until_period),
        "energy_level": info["energy"],
        "training_recommendation": info["training"],
        "nutrition_recommendation": info["nutrition"],
        "sleep_recommendation": info["sleep"],
        "phase_color": info["color"],
        "next_period_date": next_period.isoformat(),
    }


class CycleEntryCreate(BaseModel):
    cycle_start_date: date_type
    cycle_length_days: Optional[int] = 28
    period_duration_days: Optional[int] = 5
    flow_intensity: Optional[str] = "medium"  # light/medium/heavy
    symptoms: Optional[str] = None
    notes: Optional[str] = None


class CycleEntryResponse(BaseModel):
    id: str
    cycle_start_date: date_type
    cycle_length_days: Optional[int]
    period_duration_days: Optional[int]
    flow_intensity: Optional[str]
    symptoms: Optional[str]
    notes: Optional[str]
    created_at: datetime


class CycleSummaryResponse(BaseModel):
    has_data: bool
    last_cycle_start: Optional[str] = None
    avg_cycle_length: Optional[int] = None
    total_cycles_logged: int = 0
    current_phase: Optional[dict] = None
    upcoming_period: Optional[str] = None


@cycle_router.post("/entry", response_model=CycleEntryResponse, status_code=201)
async def log_cycle_entry(
    payload: CycleEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Loguer le debut d'un nouveau cycle menstruel."""
    entry_id = str(uuid.uuid4())
    await db.execute(
        text("""
            INSERT INTO menstrual_cycle_entries
                (id, user_id, cycle_start_date, cycle_length_days, period_duration_days,
                 flow_intensity, symptoms, notes, created_at, updated_at)
            VALUES
                (:id, :uid, :start, :clen, :plen, :flow, :symp, :notes, now(), now())
        """),
        {
            "id": entry_id,
            "uid": str(current_user.id),
            "start": payload.cycle_start_date,
            "clen": payload.cycle_length_days,
            "plen": payload.period_duration_days,
            "flow": payload.flow_intensity,
            "symp": payload.symptoms,
            "notes": payload.notes,
        }
    )
    await db.commit()
    return CycleEntryResponse(
        id=entry_id,
        cycle_start_date=payload.cycle_start_date,
        cycle_length_days=payload.cycle_length_days,
        period_duration_days=payload.period_duration_days,
        flow_intensity=payload.flow_intensity,
        symptoms=payload.symptoms,
        notes=payload.notes,
        created_at=datetime.now(timezone.utc),
    )


@cycle_router.get("/entries", response_model=List[CycleEntryResponse])
async def get_cycle_entries(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        text("SELECT * FROM menstrual_cycle_entries WHERE user_id = :uid ORDER BY cycle_start_date DESC LIMIT 24"),
        {"uid": str(current_user.id)}
    )
    rows = result.mappings().all()
    return [CycleEntryResponse(
        id=str(r["id"]),
        cycle_start_date=r["cycle_start_date"],
        cycle_length_days=r["cycle_length_days"],
        period_duration_days=r["period_duration_days"],
        flow_intensity=r["flow_intensity"],
        symptoms=r["symptoms"],
        notes=r["notes"],
        created_at=r["created_at"],
    ) for r in rows]


@cycle_router.get("/summary", response_model=CycleSummaryResponse)
async def get_cycle_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume du cycle avec phase actuelle et recommandations."""
    result = await db.execute(
        text("SELECT * FROM menstrual_cycle_entries WHERE user_id = :uid ORDER BY cycle_start_date DESC LIMIT 6"),
        {"uid": str(current_user.id)}
    )
    rows = result.mappings().all()

    if not rows:
        return CycleSummaryResponse(has_data=False)

    last_start = rows[0]["cycle_start_date"]
    lengths = [r["cycle_length_days"] for r in rows if r["cycle_length_days"]]
    avg_len = round(sum(lengths) / len(lengths)) if lengths else 28

    phase_info = _current_phase(last_start, avg_len)
    next_period = last_start + timedelta(days=avg_len)

    return CycleSummaryResponse(
        has_data=True,
        last_cycle_start=last_start.isoformat(),
        avg_cycle_length=avg_len,
        total_cycles_logged=len(rows),
        current_phase=phase_info,
        upcoming_period=next_period.isoformat(),
    )

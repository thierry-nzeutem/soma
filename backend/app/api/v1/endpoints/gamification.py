"""Gamification - streaks et achievements SOMA."""
from datetime import datetime, timezone, timedelta, date as date_type
from typing import Optional, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func as sqlfunc, and_, distinct
from pydantic import BaseModel
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.health import HydrationLog, HealthSample
from app.models.nutrition import NutritionEntry
from app.models.workout import WorkoutSession
from app.models.sleep import SleepSession

gamification_router = APIRouter(prefix="/gamification", tags=["Gamification"])


class StreakInfo(BaseModel):
    current: int
    best: int
    last_active: Optional[str] = None
    active_today: bool = False


class AchievementItem(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    unlocked: bool = False
    progress: Optional[float] = None  # 0-1
    unlocked_at: Optional[str] = None


class StreaksResponse(BaseModel):
    activity: StreakInfo
    nutrition_logging: StreakInfo
    hydration: StreakInfo
    sleep_logging: StreakInfo
    overall_score: int  # 0-100 composite gamification score


class GamificationResponse(BaseModel):
    streaks: StreaksResponse
    achievements: List[AchievementItem]
    level: int
    level_name: str
    xp: int
    xp_to_next_level: int
    total_days_active: int


async def _compute_streak(dates: list[date_type]) -> tuple[int, int, Optional[date_type], bool]:
    """Calcule streak courant et record depuis une liste de dates actives."""
    if not dates:
        return 0, 0, None, False

    unique_dates = sorted(set(dates), reverse=True)
    today = date_type.today()
    yesterday = today - timedelta(days=1)

    # Streak courant
    current = 0
    check = today
    active_today = unique_dates[0] == today if unique_dates else False

    if unique_dates[0] not in (today, yesterday):
        current = 0
    else:
        for d in unique_dates:
            if d == check or d == check - timedelta(days=1):
                current += 1
                check = d
            else:
                break

    # Record streak (scan complet)
    best = 0
    streak = 1
    for i in range(1, len(unique_dates)):
        if (unique_dates[i-1] - unique_dates[i]).days == 1:
            streak += 1
            best = max(best, streak)
        else:
            streak = 1
    best = max(best, current)

    return current, best, unique_dates[0] if unique_dates else None, active_today


@gamification_router.get("/streaks", response_model=StreaksResponse)
async def get_streaks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calcule les streaks d'activite, nutrition, hydratation et sommeil."""
    since = datetime.now(timezone.utc) - timedelta(days=365)
    uid = current_user.id

    # Activity streak (WorkoutSession completed OR steps > 5000)
    ws_result = await db.execute(
        select(sqlfunc.date(WorkoutSession.started_at).label("d"))
        .where(and_(WorkoutSession.user_id == uid, WorkoutSession.started_at >= since, WorkoutSession.status == "completed"))
        .distinct()
    )
    activity_dates = [r.d for r in ws_result.fetchall() if r.d]

    # Also add days with steps samples
    steps_result = await db.execute(
        select(sqlfunc.date(HealthSample.recorded_at).label("d"), sqlfunc.sum(HealthSample.value).label("total"))
        .where(and_(HealthSample.user_id == uid, HealthSample.sample_type == "steps", HealthSample.recorded_at >= since))
        .group_by(sqlfunc.date(HealthSample.recorded_at))
        .having(sqlfunc.sum(HealthSample.value) >= 5000)
    )
    activity_dates += [r.d for r in steps_result.fetchall() if r.d]

    # Nutrition logging streak
    nutr_result = await db.execute(
        select(sqlfunc.date(NutritionEntry.logged_at).label("d"))
        .where(and_(NutritionEntry.user_id == uid, NutritionEntry.logged_at >= since, NutritionEntry.is_deleted == False))
        .distinct()
    )
    nutr_dates = [r.d for r in nutr_result.fetchall() if r.d]

    # Hydration streak (at least 1 log)
    hydro_result = await db.execute(
        select(sqlfunc.date(HydrationLog.logged_at).label("d"))
        .where(and_(HydrationLog.user_id == uid, HydrationLog.logged_at >= since))
        .distinct()
    )
    hydro_dates = [r.d for r in hydro_result.fetchall() if r.d]

    # Sleep logging streak
    sleep_result = await db.execute(
        select(sqlfunc.date(SleepSession.start_at).label("d"))
        .where(and_(SleepSession.user_id == uid, SleepSession.start_at >= since))
        .distinct()
    )
    sleep_dates = [r.d for r in sleep_result.fetchall() if r.d]

    act_cur, act_best, act_last, act_today = await _compute_streak(activity_dates)
    nutr_cur, nutr_best, nutr_last, nutr_today = await _compute_streak(nutr_dates)
    hydro_cur, hydro_best, hydro_last, hydro_today = await _compute_streak(hydro_dates)
    sleep_cur, sleep_best, sleep_last, sleep_today = await _compute_streak(sleep_dates)

    def streak_score(cur: int) -> float:
        return min(cur / 30, 1.0) * 100

    overall = round(
        streak_score(act_cur) * 0.35 +
        streak_score(nutr_cur) * 0.30 +
        streak_score(hydro_cur) * 0.20 +
        streak_score(sleep_cur) * 0.15
    )

    return StreaksResponse(
        activity=StreakInfo(current=act_cur, best=act_best, last_active=act_last.isoformat() if act_last else None, active_today=act_today),
        nutrition_logging=StreakInfo(current=nutr_cur, best=nutr_best, last_active=nutr_last.isoformat() if nutr_last else None, active_today=nutr_today),
        hydration=StreakInfo(current=hydro_cur, best=hydro_best, last_active=hydro_last.isoformat() if hydro_last else None, active_today=hydro_today),
        sleep_logging=StreakInfo(current=sleep_cur, best=sleep_best, last_active=sleep_last.isoformat() if sleep_last else None, active_today=sleep_today),
        overall_score=overall,
    )


@gamification_router.get("/achievements", response_model=List[AchievementItem])
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste des achievements avec statut de deblocage."""
    uid = current_user.id

    ws_count = await db.scalar(
        select(sqlfunc.count(WorkoutSession.id))
        .where(and_(WorkoutSession.user_id == uid, WorkoutSession.status == "completed"))
    ) or 0

    nutr_count = await db.scalar(
        select(sqlfunc.count(NutritionEntry.id))
        .where(and_(NutritionEntry.user_id == uid, NutritionEntry.is_deleted == False))
    ) or 0

    sleep_count = await db.scalar(
        select(sqlfunc.count(SleepSession.id))
        .where(SleepSession.user_id == uid)
    ) or 0

    hydro_days = await db.scalar(
        select(sqlfunc.count(distinct(sqlfunc.date(HydrationLog.logged_at))))
        .where(HydrationLog.user_id == uid)
    ) or 0

    return [
        AchievementItem(id="first_workout", title="Premier pas", description="Completez votre premiere seance d'entrainement", icon="dumbbell", unlocked=ws_count >= 1, progress=min(ws_count/1, 1.0)),
        AchievementItem(id="10_workouts", title="Serie gagnante", description="Completez 10 seances d'entrainement", icon="trophy", unlocked=ws_count >= 10, progress=min(ws_count/10, 1.0)),
        AchievementItem(id="50_workouts", title="Athlete engage", description="Completez 50 seances d'entrainement", icon="medal", unlocked=ws_count >= 50, progress=min(ws_count/50, 1.0)),
        AchievementItem(id="nutrition_week", title="Semaine nutritive", description="Journalisez votre alimentation 7 jours consecutifs", icon="apple", unlocked=nutr_count >= 21, progress=min(nutr_count/21, 1.0)),
        AchievementItem(id="sleep_30", title="Sommeil de qualite", description="Loggez 30 nuits de sommeil", icon="moon", unlocked=sleep_count >= 30, progress=min(sleep_count/30, 1.0)),
        AchievementItem(id="hydration_30", title="Hydratation constante", description="Tracez votre hydratation 30 jours", icon="droplets", unlocked=hydro_days >= 30, progress=min(hydro_days/30, 1.0)),
        AchievementItem(id="centurion", title="Centurion", description="100 seances d'entrainement", icon="crown", unlocked=ws_count >= 100, progress=min(ws_count/100, 1.0)),
    ]


def _xp_from_counts(ws: int, nutr: int, sleep: int, hydro: int) -> int:
    return ws * 50 + nutr * 5 + sleep * 20 + hydro * 10


def _level_from_xp(xp: int) -> tuple[int, str, int]:
    thresholds = [0, 500, 1500, 3500, 7000, 15000, 30000]
    names = ["Debutant", "Initie", "Pratiquant", "Confirme", "Expert", "Elite", "Legende"]
    for i in range(len(thresholds) - 1, -1, -1):
        if xp >= thresholds[i]:
            next_thresh = thresholds[i+1] if i < len(thresholds)-1 else thresholds[-1] + 10000
            return i+1, names[i], next_thresh - xp
    return 1, "Debutant", 500


@gamification_router.get("/profile", response_model=GamificationResponse)
async def get_gamification_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Profil gamification complet (streaks + achievements + XP + level)."""
    uid = current_user.id
    ws_count = await db.scalar(select(sqlfunc.count(WorkoutSession.id)).where(and_(WorkoutSession.user_id == uid, WorkoutSession.status == "completed"))) or 0
    nutr_count = await db.scalar(select(sqlfunc.count(NutritionEntry.id)).where(and_(NutritionEntry.user_id == uid, NutritionEntry.is_deleted == False))) or 0
    sleep_count = await db.scalar(select(sqlfunc.count(SleepSession.id)).where(SleepSession.user_id == uid)) or 0
    hydro_days = await db.scalar(select(sqlfunc.count(distinct(sqlfunc.date(HydrationLog.logged_at)))).where(HydrationLog.user_id == uid)) or 0

    xp = _xp_from_counts(ws_count, nutr_count, sleep_count, hydro_days)
    level, level_name, xp_to_next = _level_from_xp(xp)

    since = datetime.now(timezone.utc) - timedelta(days=365)
    ws_dates_r = await db.execute(select(sqlfunc.date(WorkoutSession.started_at).label("d")).where(and_(WorkoutSession.user_id == uid, WorkoutSession.started_at >= since, WorkoutSession.status == "completed")).distinct())
    ws_dates = [r.d for r in ws_dates_r.fetchall() if r.d]
    act_cur, act_best, act_last, act_today = await _compute_streak(ws_dates)
    nutr_dates_r = await db.execute(select(sqlfunc.date(NutritionEntry.logged_at).label("d")).where(and_(NutritionEntry.user_id == uid, NutritionEntry.logged_at >= since, NutritionEntry.is_deleted == False)).distinct())
    nutr_dates = [r.d for r in nutr_dates_r.fetchall() if r.d]
    nutr_cur, nutr_best, nutr_last, nutr_today = await _compute_streak(nutr_dates)

    def streak_score(cur: int) -> float:
        return min(cur / 30, 1.0) * 100

    overall = round(streak_score(act_cur) * 0.35 + streak_score(nutr_cur) * 0.30)

    achievements = [
        AchievementItem(id="first_workout", title="Premier pas", description="Completez votre premiere seance", icon="dumbbell", unlocked=ws_count >= 1, progress=min(ws_count/1, 1.0)),
        AchievementItem(id="10_workouts", title="Serie gagnante", description="10 seances d'entrainement", icon="trophy", unlocked=ws_count >= 10, progress=min(ws_count/10, 1.0)),
        AchievementItem(id="50_workouts", title="Athlete engage", description="50 seances d'entrainement", icon="medal", unlocked=ws_count >= 50, progress=min(ws_count/50, 1.0)),
        AchievementItem(id="sleep_30", title="Sommeil de qualite", description="30 nuits journalisees", icon="moon", unlocked=sleep_count >= 30, progress=min(sleep_count/30, 1.0)),
        AchievementItem(id="hydration_30", title="Hydratation constante", description="30 jours d'hydratation trackee", icon="droplets", unlocked=hydro_days >= 30, progress=min(hydro_days/30, 1.0)),
    ]

    total_days = await db.scalar(
        select(sqlfunc.count(distinct(sqlfunc.date(NutritionEntry.logged_at))))
        .where(NutritionEntry.user_id == uid)
    ) or 0

    return GamificationResponse(
        streaks=StreaksResponse(
            activity=StreakInfo(current=act_cur, best=act_best, active_today=act_today),
            nutrition_logging=StreakInfo(current=nutr_cur, best=nutr_best, active_today=nutr_today),
            hydration=StreakInfo(current=0, best=0),
            sleep_logging=StreakInfo(current=0, best=0),
            overall_score=overall,
        ),
        achievements=achievements,
        level=level,
        level_name=level_name,
        xp=xp,
        xp_to_next_level=xp_to_next,
        total_days_active=total_days,
    )

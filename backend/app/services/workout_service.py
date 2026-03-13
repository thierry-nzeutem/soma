"""
Service workout SOMA — logique métier des sessions d'entraînement.

Responsabilités :
  - Création / mise à jour des sessions avec recalcul automatique du volume
  - Gestion des exercices et séries dans une session
  - Calcul de tonnage, volume par groupe musculaire
  - Détection des Personal Records (PR)
  - Calcul de la charge interne (Session RPE method)
  - Construction du résumé de séance (SessionSummary)
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.workout import WorkoutSession, WorkoutExercise, WorkoutSet, ExerciseLibrary
from app.schemas.workout import (
    SessionCreate, SessionUpdate, SessionDetailResponse, SessionResponse,
    SessionListResponse, SessionSummary, MuscleGroupVolume,
    ExerciseEntryCreate, ExerciseEntryUpdate, ExerciseEntryResponse,
    SetCreate, SetUpdate, SetResponse,
    ExerciseListResponse, ExerciseResponse,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _compute_tonnage(sets: List[WorkoutSet]) -> float:
    """
    Calcule le tonnage total d'une liste de séries.
    Tonnage = Σ (reps_actual × weight_kg) pour toutes les séries non warmup.
    """
    return sum(
        (s.reps_actual or 0) * (s.weight_kg or 0)
        for s in sets
        if s.reps_actual and s.weight_kg and not s.is_warmup and not s.is_deleted
    )


async def _recalculate_session_totals(db: AsyncSession, session: WorkoutSession) -> None:
    """
    Recalcule et met à jour les totaux agrégés de la session :
    total_tonnage_kg, total_sets, total_reps, internal_load_score.
    À appeler après chaque ajout/modification/suppression de set.
    """
    # Récupère tous les sets actifs de la session
    result = await db.execute(
        select(WorkoutSet)
        .join(WorkoutExercise, WorkoutSet.workout_exercise_id == WorkoutExercise.id)
        .where(and_(
            WorkoutExercise.session_id == session.id,
            WorkoutExercise.is_deleted.is_(False),
            WorkoutSet.is_deleted.is_(False),
        ))
    )
    all_sets = result.scalars().all()

    working_sets = [s for s in all_sets if not s.is_warmup]
    session.total_sets = len(working_sets)
    session.total_reps = sum(s.reps_actual or 0 for s in working_sets)
    session.total_tonnage_kg = round(_compute_tonnage(all_sets), 2) or None

    # Charge interne = durée (min) × RPE (Foster et al.)
    if session.duration_minutes and session.rpe_score:
        session.internal_load_score = round(session.duration_minutes * session.rpe_score, 1)
    else:
        session.internal_load_score = None

    await db.flush()


async def _check_pr(
    db: AsyncSession, user_id: uuid.UUID,
    exercise_id: uuid.UUID, weight_kg: float, reps_actual: int,
) -> bool:
    """
    Vérifie si le set constitue un PR (1RM estimé supérieur au précédent record).
    Utilise la formule d'Epley : 1RM = weight × (1 + reps / 30).
    """
    estimated_1rm = weight_kg * (1 + reps_actual / 30)

    # Cherche le meilleur 1RM estimé précédent pour cet exercice
    result = await db.execute(
        select(WorkoutSet.weight_kg, WorkoutSet.reps_actual)
        .join(WorkoutExercise, WorkoutSet.workout_exercise_id == WorkoutExercise.id)
        .join(WorkoutSession, WorkoutExercise.session_id == WorkoutSession.id)
        .where(and_(
            WorkoutSession.user_id == user_id,
            WorkoutExercise.exercise_id == exercise_id,
            WorkoutSet.is_deleted.is_(False),
            WorkoutSet.is_pr.is_(True),
        ))
        .order_by(WorkoutSet.created_at.desc())
        .limit(20)
    )
    previous_sets = result.fetchall()

    if not previous_sets:
        return True  # Premier set de cet exercice = PR par défaut

    best_prev_1rm = max(
        w * (1 + r / 30)
        for w, r in previous_sets
        if w and r
    ) if previous_sets else 0

    return estimated_1rm > best_prev_1rm


# ── Exercise Library ────────────────────────────────────────────────────────────

async def list_exercises(
    db: AsyncSession,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    equipment: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
) -> ExerciseListResponse:
    """Récupère la bibliothèque d'exercices avec filtres optionnels."""
    q = select(ExerciseLibrary)

    if category:
        q = q.where(ExerciseLibrary.category == category)
    if difficulty:
        q = q.where(ExerciseLibrary.difficulty_level == difficulty)
    if search:
        q = q.where(
            ExerciseLibrary.name.ilike(f"%{search}%")
            | ExerciseLibrary.name_fr.ilike(f"%{search}%")
        )

    # Count total
    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    q = q.order_by(ExerciseLibrary.name).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    exercises = result.scalars().all()

    return ExerciseListResponse(
        exercises=[ExerciseResponse.model_validate(e) for e in exercises],
        total=total,
    )


async def get_exercise(db: AsyncSession, exercise_id: uuid.UUID) -> Optional[ExerciseLibrary]:
    result = await db.execute(select(ExerciseLibrary).where(ExerciseLibrary.id == exercise_id))
    return result.scalar_one_or_none()


# ── Workout Sessions ───────────────────────────────────────────────────────────

async def create_session(
    db: AsyncSession, user_id: uuid.UUID, data: SessionCreate,
) -> WorkoutSession:
    """Crée une nouvelle session d'entraînement."""
    session = WorkoutSession(
        user_id=user_id,
        started_at=data.started_at or datetime.now(timezone.utc),
        session_type=data.session_type,
        location=data.location,
        status=data.status,
        notes=data.notes,
        energy_before=data.energy_before,
        is_completed=data.status == "completed",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID,
) -> Optional[WorkoutSession]:
    """Récupère une session par ID (filtre utilisateur + soft delete)."""
    result = await db.execute(
        select(WorkoutSession).where(and_(
            WorkoutSession.id == session_id,
            WorkoutSession.user_id == user_id,
            WorkoutSession.is_deleted.is_(False),
        ))
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession, user_id: uuid.UUID,
    page: int = 1, per_page: int = 20,
    session_type: Optional[str] = None,
    status: Optional[str] = None,
) -> SessionListResponse:
    """Liste les sessions de l'utilisateur avec pagination."""
    q = select(WorkoutSession).where(and_(
        WorkoutSession.user_id == user_id,
        WorkoutSession.is_deleted.is_(False),
    ))
    if session_type:
        q = q.where(WorkoutSession.session_type == session_type)
    if status:
        q = q.where(WorkoutSession.status == status)

    count_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = count_result.scalar() or 0

    q = q.order_by(WorkoutSession.started_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    sessions = result.scalars().all()

    return SessionListResponse(
        sessions=[SessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
    )


async def update_session(
    db: AsyncSession, session: WorkoutSession, data: SessionUpdate,
) -> WorkoutSession:
    """Met à jour les métadonnées d'une session."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)

    # Sync is_completed avec status
    if "status" in update_data:
        session.is_completed = update_data["status"] == "completed"

    # Auto-calcul durée si ended_at fourni sans duration_minutes
    if session.ended_at and session.started_at and not session.duration_minutes:
        delta = session.ended_at - session.started_at
        session.duration_minutes = int(delta.total_seconds() / 60)

    await _recalculate_session_totals(db, session)
    return session


async def delete_session(db: AsyncSession, session: WorkoutSession) -> None:
    """Soft-delete une session (et ses exercices/sets par cascade logique)."""
    session.is_deleted = True
    # Soft-delete des exercices et sets associés
    exercises_result = await db.execute(
        select(WorkoutExercise).where(WorkoutExercise.session_id == session.id)
    )
    exercises = exercises_result.scalars().all()
    for ex in exercises:
        ex.is_deleted = True
        sets_result = await db.execute(
            select(WorkoutSet).where(WorkoutSet.workout_exercise_id == ex.id)
        )
        for s in sets_result.scalars().all():
            s.is_deleted = True
    await db.flush()


async def get_session_detail(
    db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID,
) -> Optional[SessionDetailResponse]:
    """Récupère une session avec tous ses exercices et séries imbriqués."""
    session = await get_session(db, session_id, user_id)
    if not session:
        return None

    # Exercices actifs avec leurs sets
    ex_result = await db.execute(
        select(WorkoutExercise)
        .where(and_(
            WorkoutExercise.session_id == session_id,
            WorkoutExercise.is_deleted.is_(False),
        ))
        .order_by(WorkoutExercise.exercise_order)
    )
    exercises_orm = ex_result.scalars().all()

    exercises_out = []
    for ex in exercises_orm:
        sets_result = await db.execute(
            select(WorkoutSet)
            .where(and_(
                WorkoutSet.workout_exercise_id == ex.id,
                WorkoutSet.is_deleted.is_(False),
            ))
            .order_by(WorkoutSet.set_number)
        )
        sets_orm = sets_result.scalars().all()
        ex_response = ExerciseEntryResponse.model_validate(ex)
        ex_response.sets = [SetResponse.model_validate(s) for s in sets_orm]
        # Recalcul des champs dérivés
        ex_response.total_sets = len(ex_response.sets)
        ex_response.total_reps = sum(s.reps_actual or 0 for s in ex_response.sets)
        ex_response.tonnage_kg = sum(
            (s.reps_actual or 0) * (s.weight_kg or 0)
            for s in ex_response.sets
            if s.reps_actual and s.weight_kg
        ) or None
        exercises_out.append(ex_response)

    detail = SessionDetailResponse.model_validate(session)
    detail.exercises = exercises_out
    return detail


# ── Exercises in session ────────────────────────────────────────────────────────

async def add_exercise_to_session(
    db: AsyncSession, session: WorkoutSession, data: ExerciseEntryCreate,
) -> WorkoutExercise:
    """Ajoute un exercice à une session."""
    entry = WorkoutExercise(
        session_id=session.id,
        exercise_id=data.exercise_id,
        exercise_order=data.exercise_order,
        notes=data.notes,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def update_exercise_entry(
    db: AsyncSession, entry: WorkoutExercise, data: ExerciseEntryUpdate,
) -> WorkoutExercise:
    """Met à jour les métadonnées d'un exercice dans une session."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    await db.flush()
    return entry


async def remove_exercise_from_session(
    db: AsyncSession, entry: WorkoutExercise, session: WorkoutSession,
) -> None:
    """Soft-delete un exercice et ses séries, puis recalcule les totaux."""
    entry.is_deleted = True
    sets_result = await db.execute(
        select(WorkoutSet).where(WorkoutSet.workout_exercise_id == entry.id)
    )
    for s in sets_result.scalars().all():
        s.is_deleted = True
    await _recalculate_session_totals(db, session)


async def get_exercise_entry(
    db: AsyncSession, entry_id: uuid.UUID, session_id: uuid.UUID,
) -> Optional[WorkoutExercise]:
    result = await db.execute(
        select(WorkoutExercise).where(and_(
            WorkoutExercise.id == entry_id,
            WorkoutExercise.session_id == session_id,
            WorkoutExercise.is_deleted.is_(False),
        ))
    )
    return result.scalar_one_or_none()


# ── Sets ───────────────────────────────────────────────────────────────────────

async def add_set(
    db: AsyncSession, entry: WorkoutExercise, session: WorkoutSession,
    data: SetCreate, user_id: uuid.UUID,
) -> WorkoutSet:
    """
    Ajoute une série à un exercice.
    Vérifie automatiquement si c'est un PR (si exercice de la bibliothèque).
    """
    is_pr = False
    if (
        entry.exercise_id
        and data.weight_kg
        and data.reps_actual
        and not data.is_warmup
    ):
        is_pr = await _check_pr(db, user_id, entry.exercise_id, data.weight_kg, data.reps_actual)

    new_set = WorkoutSet(
        workout_exercise_id=entry.id,
        set_number=data.set_number,
        reps_target=data.reps_target,
        reps_actual=data.reps_actual,
        weight_kg=data.weight_kg,
        duration_seconds=data.duration_seconds,
        rest_seconds=data.rest_seconds,
        tempo=data.tempo,
        rpe_set=data.rpe_set,
        is_warmup=data.is_warmup,
        is_pr=is_pr,
        data_source=data.data_source,
    )
    db.add(new_set)
    await db.flush()

    # Recalcul des totaux session
    await _recalculate_session_totals(db, session)
    await db.refresh(new_set)
    return new_set


async def update_set(
    db: AsyncSession, workout_set: WorkoutSet, session: WorkoutSession,
    data: SetUpdate,
) -> WorkoutSet:
    """Met à jour une série et recalcule les totaux."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workout_set, field, value)
    await db.flush()
    await _recalculate_session_totals(db, session)
    await db.refresh(workout_set)
    return workout_set


async def delete_set(
    db: AsyncSession, workout_set: WorkoutSet, session: WorkoutSession,
) -> None:
    """Soft-delete une série et recalcule les totaux."""
    workout_set.is_deleted = True
    await _recalculate_session_totals(db, session)


async def get_set(
    db: AsyncSession, set_id: uuid.UUID, entry_id: uuid.UUID,
) -> Optional[WorkoutSet]:
    result = await db.execute(
        select(WorkoutSet).where(and_(
            WorkoutSet.id == set_id,
            WorkoutSet.workout_exercise_id == entry_id,
            WorkoutSet.is_deleted.is_(False),
        ))
    )
    return result.scalar_one_or_none()


# ── Session Summary ─────────────────────────────────────────────────────────────

async def get_session_summary(
    db: AsyncSession, session: WorkoutSession,
) -> SessionSummary:
    """
    Construit le résumé détaillé d'une session terminée.
    Inclut volume global, volume par groupe musculaire, PRs et charge interne.
    """
    # Exercices actifs
    ex_result = await db.execute(
        select(WorkoutExercise)
        .where(and_(
            WorkoutExercise.session_id == session.id,
            WorkoutExercise.is_deleted.is_(False),
        ))
    )
    exercises = ex_result.scalars().all()

    # Sets actifs de chaque exercice
    all_sets: List[WorkoutSet] = []
    prs: List[dict] = []
    muscle_volumes: Dict[str, Dict] = {}

    for ex in exercises:
        sets_result = await db.execute(
            select(WorkoutSet)
            .where(and_(
                WorkoutSet.workout_exercise_id == ex.id,
                WorkoutSet.is_deleted.is_(False),
            ))
        )
        sets = sets_result.scalars().all()
        all_sets.extend(sets)

        # PRs
        for s in sets:
            if s.is_pr and s.weight_kg and s.reps_actual:
                estimated_1rm = round(s.weight_kg * (1 + s.reps_actual / 30), 1)
                prs.append({
                    "exercise_id": str(ex.exercise_id) if ex.exercise_id else None,
                    "weight_kg": s.weight_kg,
                    "reps": s.reps_actual,
                    "estimated_1rm_kg": estimated_1rm,
                })

        # Volume par groupe musculaire (via ExerciseLibrary)
        if ex.exercise_id:
            lib_result = await db.execute(
                select(ExerciseLibrary).where(ExerciseLibrary.id == ex.exercise_id)
            )
            lib = lib_result.scalar_one_or_none()
            if lib and lib.primary_muscles:
                working_sets = [s for s in sets if not s.is_warmup and not s.is_deleted]
                tonnage = _compute_tonnage(sets)
                total_reps = sum(s.reps_actual or 0 for s in working_sets)
                for muscle in lib.primary_muscles:
                    if muscle not in muscle_volumes:
                        muscle_volumes[muscle] = {"sets": 0, "reps": 0, "tonnage": 0.0}
                    muscle_volumes[muscle]["sets"] += len(working_sets)
                    muscle_volumes[muscle]["reps"] += total_reps
                    muscle_volumes[muscle]["tonnage"] += tonnage

    # Agrégats globaux
    working_sets = [s for s in all_sets if not s.is_warmup and not s.is_deleted]
    total_sets = len(working_sets)
    total_reps = sum(s.reps_actual or 0 for s in working_sets)
    total_tonnage = round(_compute_tonnage(all_sets), 2)

    rpe_values = [s.rpe_set for s in working_sets if s.rpe_set]
    avg_rpe = round(sum(rpe_values) / len(rpe_values), 1) if rpe_values else None

    # Volume par groupe musculaire — tri par tonnage décroissant
    volume_by_muscle = [
        MuscleGroupVolume(
            muscle_group=muscle,
            total_sets=v["sets"],
            total_reps=v["reps"],
            tonnage_kg=round(v["tonnage"], 1),
        )
        for muscle, v in sorted(muscle_volumes.items(), key=lambda x: x[1]["tonnage"], reverse=True)
    ]

    # Résumé textuel
    summary_parts = [
        f"{len(exercises)} exercice(s)",
        f"{total_sets} séries",
        f"{total_tonnage:.0f}kg de tonnage",
    ]
    if session.duration_minutes:
        summary_parts.append(f"{session.duration_minutes}min")
    if prs:
        summary_parts.append(f"{len(prs)} PR(s) !")
    summary_text = " · ".join(summary_parts)

    return SessionSummary(
        session_id=session.id,
        date=str(session.started_at.date()),
        duration_minutes=session.duration_minutes,
        session_type=session.session_type,
        status=session.status,
        total_exercises=len(exercises),
        total_sets=total_sets,
        total_reps=total_reps,
        total_tonnage_kg=total_tonnage,
        avg_rpe=avg_rpe,
        distance_km=session.distance_km,
        calories_burned_kcal=session.calories_burned_kcal,
        internal_load_score=session.internal_load_score,
        volume_by_muscle_group=volume_by_muscle,
        personal_records=prs,
        summary_text=summary_text,
    )

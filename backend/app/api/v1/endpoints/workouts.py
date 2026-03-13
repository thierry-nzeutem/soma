"""
Endpoints workout SOMA — Module G (Sessions, Exercices, Séries).

Routes exposées :
  GET    /exercises                    — bibliothèque d'exercices
  GET    /exercises/{id}               — détail d'un exercice

  POST   /sessions                     — créer une session
  GET    /sessions                     — lister ses sessions
  GET    /sessions/{id}                — détail complet d'une session
  PATCH  /sessions/{id}                — mettre à jour une session
  DELETE /sessions/{id}                — supprimer (soft) une session
  GET    /sessions/{id}/summary        — résumé enrichi (tonnage, PRs, groupes musculaires)

  POST   /sessions/{id}/exercises                        — ajouter un exercice
  PATCH  /sessions/{id}/exercises/{ex_id}                — MAJ un exercice
  DELETE /sessions/{id}/exercises/{ex_id}                — supprimer (soft) un exercice

  POST   /sessions/{id}/exercises/{ex_id}/sets           — ajouter une série
  PATCH  /sessions/{id}/exercises/{ex_id}/sets/{set_id}  — MAJ une série
  DELETE /sessions/{id}/exercises/{ex_id}/sets/{set_id}  — supprimer une série
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.workout import (
    ExerciseResponse, ExerciseListResponse,
    SessionCreate, SessionUpdate, SessionResponse, SessionDetailResponse,
    SessionListResponse, SessionSummary,
    ExerciseEntryCreate, ExerciseEntryUpdate, ExerciseEntryResponse,
    SetCreate, SetUpdate, SetResponse,
)
from app.services import workout_service as svc

# ── Routeurs ───────────────────────────────────────────────────────────────────

exercises_router = APIRouter(prefix="/exercises", tags=["exercises"])
sessions_router = APIRouter(prefix="/sessions", tags=["workouts"])


# ── Exercise Library ────────────────────────────────────────────────────────────

@exercises_router.get("", response_model=ExerciseListResponse, summary="Bibliothèque d'exercices")
async def list_exercises(
    category: Optional[str] = Query(None, description="Filtre par catégorie (strength, cardio, mobility…)"),
    difficulty: Optional[str] = Query(None, description="Filtre par difficulté (beginner, intermediate, advanced)"),
    search: Optional[str] = Query(None, description="Recherche textuelle sur nom / nom_fr"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ExerciseListResponse:
    return await svc.list_exercises(db, category=category, difficulty=difficulty, search=search, page=page, per_page=per_page)


@exercises_router.get("/{exercise_id}", response_model=ExerciseResponse, summary="Détail d'un exercice")
async def get_exercise(
    exercise_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ExerciseResponse:
    exercise = await svc.get_exercise(db, exercise_id)
    if not exercise:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    return ExerciseResponse.model_validate(exercise)


# ── Sessions ───────────────────────────────────────────────────────────────────

@sessions_router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Créer une session")
async def create_session(
    data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await svc.create_session(db, current_user.id, data)
    await db.commit()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@sessions_router.get("", response_model=SessionListResponse, summary="Lister les sessions")
async def list_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    session_type: Optional[str] = Query(None, description="Filtre par type (strength, cardio…)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filtre par statut"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    return await svc.list_sessions(db, current_user.id, page=page, per_page=per_page, session_type=session_type, status=status_filter)


@sessions_router.get("/{session_id}", response_model=SessionDetailResponse, summary="Détail d'une session")
async def get_session_detail(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionDetailResponse:
    detail = await svc.get_session_detail(db, session_id, current_user.id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    return detail


@sessions_router.patch("/{session_id}", response_model=SessionResponse, summary="Mettre à jour une session")
async def update_session(
    session_id: uuid.UUID,
    data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    session = await svc.update_session(db, session, data)
    await db.commit()
    await db.refresh(session)
    return SessionResponse.model_validate(session)


@sessions_router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Supprimer une session")
async def delete_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    await svc.delete_session(db, session)
    await db.commit()


@sessions_router.get("/{session_id}/summary", response_model=SessionSummary, summary="Résumé enrichi d'une session")
async def get_session_summary(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SessionSummary:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    return await svc.get_session_summary(db, session)


# ── Exercices dans une session ──────────────────────────────────────────────────

@sessions_router.post(
    "/{session_id}/exercises",
    response_model=ExerciseEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un exercice à une session",
)
async def add_exercise(
    session_id: uuid.UUID,
    data: ExerciseEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseEntryResponse:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    entry = await svc.add_exercise_to_session(db, session, data)
    await db.commit()
    await db.refresh(entry)
    response = ExerciseEntryResponse.model_validate(entry)
    response.sets = []
    return response


@sessions_router.patch(
    "/{session_id}/exercises/{entry_id}",
    response_model=ExerciseEntryResponse,
    summary="Mettre à jour un exercice dans une session",
)
async def update_exercise(
    session_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: ExerciseEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExerciseEntryResponse:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    entry = await svc.get_exercise_entry(db, entry_id, session_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable dans cette session")
    entry = await svc.update_exercise_entry(db, entry, data)
    await db.commit()
    await db.refresh(entry)
    response = ExerciseEntryResponse.model_validate(entry)
    response.sets = []
    return response


@sessions_router.delete(
    "/{session_id}/exercises/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un exercice d'une session",
)
async def remove_exercise(
    session_id: uuid.UUID,
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    entry = await svc.get_exercise_entry(db, entry_id, session_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable dans cette session")
    await svc.remove_exercise_from_session(db, entry, session)
    await db.commit()


# ── Séries ────────────────────────────────────────────────────────────────────

@sessions_router.post(
    "/{session_id}/exercises/{entry_id}/sets",
    response_model=SetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une série à un exercice",
)
async def add_set(
    session_id: uuid.UUID,
    entry_id: uuid.UUID,
    data: SetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SetResponse:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    entry = await svc.get_exercise_entry(db, entry_id, session_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable dans cette session")
    new_set = await svc.add_set(db, entry, session, data, current_user.id)
    await db.commit()
    await db.refresh(new_set)
    return SetResponse.model_validate(new_set)


@sessions_router.patch(
    "/{session_id}/exercises/{entry_id}/sets/{set_id}",
    response_model=SetResponse,
    summary="Mettre à jour une série",
)
async def update_set(
    session_id: uuid.UUID,
    entry_id: uuid.UUID,
    set_id: uuid.UUID,
    data: SetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SetResponse:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    entry = await svc.get_exercise_entry(db, entry_id, session_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    workout_set = await svc.get_set(db, set_id, entry_id)
    if not workout_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Série introuvable")
    workout_set = await svc.update_set(db, workout_set, session, data)
    await db.commit()
    await db.refresh(workout_set)
    return SetResponse.model_validate(workout_set)


@sessions_router.delete(
    "/{session_id}/exercises/{entry_id}/sets/{set_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une série",
)
async def delete_set(
    session_id: uuid.UUID,
    entry_id: uuid.UUID,
    set_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    session = await svc.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session introuvable")
    entry = await svc.get_exercise_entry(db, entry_id, session_id)
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercice introuvable")
    workout_set = await svc.get_set(db, set_id, entry_id)
    if not workout_set:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Série introuvable")
    await svc.delete_set(db, workout_set, session)
    await db.commit()

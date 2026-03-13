"""
Endpoint Vision Sessions — LOT 7 Computer Vision.

Périmètre :
  - POST /vision/sessions : enregistre le résumé d'une session CV mobile
  - GET  /vision/sessions : liste les sessions de l'utilisateur (historique)
"""
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.vision_session import VisionSession
from app.schemas.vision import VisionSessionCreate, VisionSessionResponse


vision_router = APIRouter(prefix="/vision", tags=["Computer Vision"])


# ── POST /vision/sessions ──────────────────────────────────────────────────────

@vision_router.post(
    "/sessions",
    response_model=VisionSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistre une session Computer Vision",
    description=(
        "Reçoit le résumé JSON calculé côté mobile (rep count, durée, scores "
        "biomécaniques). Aucune vidéo n'est transmise au serveur."
    ),
)
async def create_vision_session(
    body: VisionSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VisionSessionResponse:
    """
    Sauvegarde un résumé de session Computer Vision.

    Le mobile envoie uniquement les métriques calculées localement :
    - Exercice, répétitions, durée
    - Scores biomécaniques amplitude / stabilité / régularité / global
    - Optionnel : ID de la WorkoutSession à laquelle rattacher la session

    Retourne la session créée avec son ID et la date de session.
    """
    # Extraction de l'algorithm_version depuis metadata si présent
    algo_version = body.metadata.get("algorithm_version", "v1.0")

    session = VisionSession(
        user_id=current_user.id,
        exercise_type=body.exercise_type,
        rep_count=body.reps,
        duration_seconds=body.duration_seconds,
        amplitude_score=body.amplitude_score,
        stability_score=body.stability_score,
        regularity_score=body.regularity_score,
        quality_score=body.quality_score,
        workout_session_id=body.workout_session_id,
        metadata_=body.metadata,
        algorithm_version=algo_version,
        session_date=date.today(),
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return VisionSessionResponse(
        id=session.id,
        exercise_type=session.exercise_type,
        reps=session.rep_count,
        duration_seconds=session.duration_seconds,
        amplitude_score=session.amplitude_score,
        stability_score=session.stability_score,
        regularity_score=session.regularity_score,
        quality_score=session.quality_score,
        workout_session_id=session.workout_session_id,
        algorithm_version=session.algorithm_version,
        session_date=session.session_date,
        created_at=session.created_at,
    )


# ── GET /vision/sessions ───────────────────────────────────────────────────────

@vision_router.get(
    "/sessions",
    response_model=List[VisionSessionResponse],
    summary="Liste les sessions Computer Vision de l'utilisateur",
)
async def list_vision_sessions(
    exercise_type: Optional[str] = Query(None, description="Filtre par exercice"),
    from_date: Optional[str] = Query(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Date de début (YYYY-MM-DD)",
    ),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de sessions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[VisionSessionResponse]:
    """
    Retourne l'historique des sessions Computer Vision de l'utilisateur.

    Filtres disponibles :
    - `exercise_type` : exercice spécifique (squat, push_up…)
    - `from_date` : sessions depuis cette date (YYYY-MM-DD)
    - `limit` : max résultats (défaut 50)
    """
    filters = [VisionSession.user_id == current_user.id]

    if exercise_type:
        filters.append(VisionSession.exercise_type == exercise_type)

    if from_date:
        try:
            start = datetime.strptime(from_date, "%Y-%m-%d").date()
            filters.append(VisionSession.session_date >= start)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="from_date format invalide. Utiliser YYYY-MM-DD.",
            )

    result = await db.execute(
        select(VisionSession)
        .where(and_(*filters))
        .order_by(VisionSession.created_at.desc())
        .limit(limit)
    )
    sessions = result.scalars().all()

    return [
        VisionSessionResponse(
            id=s.id,
            exercise_type=s.exercise_type,
            reps=s.rep_count,
            duration_seconds=s.duration_seconds,
            amplitude_score=s.amplitude_score,
            stability_score=s.stability_score,
            regularity_score=s.regularity_score,
            quality_score=s.quality_score,
            workout_session_id=s.workout_session_id,
            algorithm_version=s.algorithm_version,
            session_date=s.session_date,
            created_at=s.created_at,
        )
        for s in sessions
    ]

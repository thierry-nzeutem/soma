"""
Schemas Pydantic — VisionSession (LOT 7 Computer Vision).

Reçoit le résumé JSON d'une session mobile (rep count, durée, scores)
et retourne la confirmation de sauvegarde avec l'ID généré.
"""
import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Création ───────────────────────────────────────────────────────────────────

class VisionSessionCreate(BaseModel):
    """Corps de la requête POST /vision/sessions."""

    # Exercice (snake_case côté mobile)
    exercise_type: str = Field(
        ...,
        description="Type d'exercice (squat, push_up, plank, jumping_jack, lunge, sit_up).",
        examples=["squat"],
    )

    # Métriques de performance
    reps: int = Field(
        default=0,
        ge=0,
        description="Nombre de répétitions comptées.",
        alias="reps",
    )
    duration_seconds: int = Field(
        default=0,
        ge=0,
        description="Durée de la session en secondes.",
    )

    # Scores biomécaniques [0-100]
    amplitude_score: Optional[float] = Field(
        None, ge=0, le=100, description="Score amplitude de mouvement."
    )
    stability_score: Optional[float] = Field(
        None, ge=0, le=100, description="Score stabilité posturale."
    )
    regularity_score: Optional[float] = Field(
        None, ge=0, le=100, description="Score régularité du rythme."
    )
    quality_score: Optional[float] = Field(
        None, ge=0, le=100, description="Score global biomécanique."
    )

    # Rattachement workout
    workout_session_id: Optional[uuid.UUID] = Field(
        None, description="ID de la WorkoutSession à laquelle rattacher la session."
    )

    # Métadonnées libres (algorithme, device, etc.)
    metadata: dict = Field(default_factory=dict)

    @field_validator("exercise_type")
    @classmethod
    def validate_exercise_type(cls, v: str) -> str:
        allowed = {"squat", "push_up", "plank", "jumping_jack", "lunge", "sit_up"}
        if v not in allowed:
            raise ValueError(
                f"exercise_type must be one of {allowed}, got '{v}'"
            )
        return v

    model_config = {"populate_by_name": True}


# ── Réponse ────────────────────────────────────────────────────────────────────

class VisionSessionResponse(BaseModel):
    """Réponse après création d'une session vision."""

    id: uuid.UUID
    exercise_type: str
    reps: int
    duration_seconds: int
    amplitude_score: Optional[float]
    stability_score: Optional[float]
    regularity_score: Optional[float]
    quality_score: Optional[float]
    workout_session_id: Optional[uuid.UUID]
    algorithm_version: str
    session_date: date
    created_at: datetime

    model_config = {"from_attributes": True}

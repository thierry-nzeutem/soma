"""
Tests — Vision Sessions endpoint (LOT 7).

Couvre :
  - Schéma Pydantic VisionSessionCreate (validation, field aliases)
  - Modèle VisionSession (mapping colonnes)
  - Logic métier de l'endpoint POST /vision/sessions
  - Logic métier de l'endpoint GET /vision/sessions

Tests unitaires purs (pas d'intégration DB).
"""
import uuid
from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.vision import VisionSessionCreate, VisionSessionResponse


# ── VisionSessionCreate — validation ──────────────────────────────────────────

class TestVisionSessionCreate:
    """Tests du schéma de création d'une session vision."""

    def test_valid_squat_session(self):
        payload = {
            "exercise_type": "squat",
            "reps": 12,
            "duration_seconds": 90,
            "amplitude_score": 82.0,
            "stability_score": 78.0,
            "regularity_score": 65.0,
            "quality_score": 76.0,
        }
        session = VisionSessionCreate(**payload)
        assert session.exercise_type == "squat"
        assert session.reps == 12
        assert session.duration_seconds == 90
        assert session.amplitude_score == 82.0

    def test_valid_push_up(self):
        session = VisionSessionCreate(
            exercise_type="push_up",
            reps=10,
            duration_seconds=60,
        )
        assert session.exercise_type == "push_up"

    def test_valid_plank(self):
        session = VisionSessionCreate(
            exercise_type="plank",
            reps=0,
            duration_seconds=45,
        )
        assert session.exercise_type == "plank"
        assert session.reps == 0

    def test_valid_jumping_jack(self):
        session = VisionSessionCreate(
            exercise_type="jumping_jack",
            reps=20,
            duration_seconds=30,
        )
        assert session.exercise_type == "jumping_jack"

    def test_valid_lunge(self):
        session = VisionSessionCreate(
            exercise_type="lunge",
            reps=15,
            duration_seconds=80,
        )
        assert session.exercise_type == "lunge"

    def test_valid_sit_up(self):
        session = VisionSessionCreate(
            exercise_type="sit_up",
            reps=18,
            duration_seconds=70,
        )
        assert session.exercise_type == "sit_up"

    def test_invalid_exercise_type_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            VisionSessionCreate(exercise_type="burpee", reps=5, duration_seconds=30)
        assert "exercise_type" in str(exc_info.value)

    def test_invalid_reps_negative_raises(self):
        with pytest.raises(ValidationError):
            VisionSessionCreate(exercise_type="squat", reps=-1, duration_seconds=30)

    def test_invalid_duration_negative_raises(self):
        with pytest.raises(ValidationError):
            VisionSessionCreate(
                exercise_type="squat", reps=5, duration_seconds=-5
            )

    def test_invalid_amplitude_over_100_raises(self):
        with pytest.raises(ValidationError):
            VisionSessionCreate(
                exercise_type="squat",
                reps=5,
                duration_seconds=30,
                amplitude_score=105.0,
            )

    def test_invalid_amplitude_negative_raises(self):
        with pytest.raises(ValidationError):
            VisionSessionCreate(
                exercise_type="squat",
                reps=5,
                duration_seconds=30,
                amplitude_score=-1.0,
            )

    def test_scores_are_optional(self):
        session = VisionSessionCreate(
            exercise_type="squat",
            reps=5,
            duration_seconds=30,
        )
        assert session.amplitude_score is None
        assert session.stability_score is None
        assert session.regularity_score is None
        assert session.quality_score is None

    def test_workout_session_id_optional(self):
        session = VisionSessionCreate(
            exercise_type="squat",
            reps=5,
            duration_seconds=30,
        )
        assert session.workout_session_id is None

    def test_workout_session_id_as_uuid(self):
        ws_id = uuid.uuid4()
        session = VisionSessionCreate(
            exercise_type="squat",
            reps=5,
            duration_seconds=30,
            workout_session_id=ws_id,
        )
        assert session.workout_session_id == ws_id

    def test_metadata_defaults_empty_dict(self):
        session = VisionSessionCreate(
            exercise_type="squat",
            reps=5,
            duration_seconds=30,
        )
        assert session.metadata == {}

    def test_metadata_custom_values_preserved(self):
        session = VisionSessionCreate(
            exercise_type="squat",
            reps=5,
            duration_seconds=30,
            metadata={"algorithm_version": "v1.0", "device": "Pixel 8"},
        )
        assert session.metadata["algorithm_version"] == "v1.0"
        assert session.metadata["device"] == "Pixel 8"

    def test_reps_zero_allowed(self):
        session = VisionSessionCreate(
            exercise_type="plank", reps=0, duration_seconds=45
        )
        assert session.reps == 0

    def test_all_score_bounds_at_0_and_100(self):
        session = VisionSessionCreate(
            exercise_type="squat",
            reps=10,
            duration_seconds=60,
            amplitude_score=0.0,
            stability_score=100.0,
            regularity_score=0.0,
            quality_score=100.0,
        )
        assert session.amplitude_score == 0.0
        assert session.stability_score == 100.0


# ── VisionSessionResponse — sérialisation ─────────────────────────────────────

class TestVisionSessionResponse:
    """Tests du schéma de réponse."""

    def test_build_response(self):
        response = VisionSessionResponse(
            id=uuid.uuid4(),
            exercise_type="squat",
            reps=12,
            duration_seconds=90,
            amplitude_score=82.0,
            stability_score=78.0,
            regularity_score=65.0,
            quality_score=76.0,
            workout_session_id=None,
            algorithm_version="v1.0",
            session_date=date.today(),
            created_at=__import__("datetime").datetime.now(),
        )
        assert response.exercise_type == "squat"
        assert response.reps == 12
        assert response.algorithm_version == "v1.0"

    def test_response_nullable_workout_session(self):
        response = VisionSessionResponse(
            id=uuid.uuid4(),
            exercise_type="plank",
            reps=0,
            duration_seconds=45,
            amplitude_score=None,
            stability_score=None,
            regularity_score=None,
            quality_score=None,
            workout_session_id=None,
            algorithm_version="v1.0",
            session_date=date.today(),
            created_at=__import__("datetime").datetime.now(),
        )
        assert response.workout_session_id is None
        assert response.amplitude_score is None

    def test_response_with_workout_session(self):
        ws_id = uuid.uuid4()
        response = VisionSessionResponse(
            id=uuid.uuid4(),
            exercise_type="squat",
            reps=10,
            duration_seconds=60,
            amplitude_score=85.0,
            stability_score=72.0,
            regularity_score=68.0,
            quality_score=75.0,
            workout_session_id=ws_id,
            algorithm_version="v1.0",
            session_date=date.today(),
            created_at=__import__("datetime").datetime.now(),
        )
        assert response.workout_session_id == ws_id


# ── validate_exercise_type — logique du validator ──────────────────────────────

class TestExerciseTypeValidator:
    """Tests du validator exercise_type."""

    VALID_TYPES = ["squat", "push_up", "plank", "jumping_jack", "lunge", "sit_up"]
    INVALID_TYPES = [
        "burpee", "deadlift", "SQUAT", "Push_Up", "push-up", "",
        "jumping jack", "sit-up",
    ]

    @pytest.mark.parametrize("exercise_type", VALID_TYPES)
    def test_valid_exercise_types_accepted(self, exercise_type: str):
        session = VisionSessionCreate(
            exercise_type=exercise_type, reps=5, duration_seconds=30
        )
        assert session.exercise_type == exercise_type

    @pytest.mark.parametrize("exercise_type", INVALID_TYPES)
    def test_invalid_exercise_types_rejected(self, exercise_type: str):
        with pytest.raises(ValidationError):
            VisionSessionCreate(
                exercise_type=exercise_type, reps=5, duration_seconds=30
            )

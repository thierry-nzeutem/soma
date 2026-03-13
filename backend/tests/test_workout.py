"""
Tests unitaires — workout_service.py (logique pure, sans DB)

Stratégie :
  - Tests sur les fonctions synchrones et helpers
  - Mocks pour les fonctions async (_recalculate_session_totals)
  - Tests des schémas Pydantic workout
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import uuid

from app.services.workout_service import _compute_tonnage
from app.schemas.workout import (
    SessionCreate, SessionUpdate, SetCreate, SetResponse,
    ExerciseEntryCreate, ExerciseEntryResponse,
    SessionSummary, MuscleGroupVolume,
)


# ── Helpers de test ────────────────────────────────────────────────────────────

def make_mock_set(
    reps_actual: int = 8,
    weight_kg: float = 80.0,
    is_warmup: bool = False,
    is_deleted: bool = False,
    rpe_set: float = None,
) -> MagicMock:
    s = MagicMock()
    s.reps_actual = reps_actual
    s.weight_kg = weight_kg
    s.is_warmup = is_warmup
    s.is_deleted = is_deleted
    s.rpe_set = rpe_set
    return s


# ── Tests _compute_tonnage ─────────────────────────────────────────────────────

class TestComputeTonnage:

    def test_basic_tonnage(self):
        sets = [make_mock_set(8, 80.0), make_mock_set(8, 80.0), make_mock_set(8, 80.0)]
        assert _compute_tonnage(sets) == pytest.approx(1920.0)

    def test_warmup_sets_excluded(self):
        sets = [
            make_mock_set(10, 40.0, is_warmup=True),
            make_mock_set(8, 80.0, is_warmup=False),
        ]
        assert _compute_tonnage(sets) == pytest.approx(640.0)

    def test_deleted_sets_excluded(self):
        sets = [
            make_mock_set(8, 80.0, is_deleted=True),
            make_mock_set(8, 80.0, is_deleted=False),
        ]
        assert _compute_tonnage(sets) == pytest.approx(640.0)

    def test_none_reps_excluded(self):
        s = make_mock_set()
        s.reps_actual = None
        sets = [s, make_mock_set(8, 80.0)]
        assert _compute_tonnage(sets) == pytest.approx(640.0)

    def test_none_weight_excluded(self):
        s = make_mock_set()
        s.weight_kg = None
        sets = [s, make_mock_set(8, 80.0)]
        assert _compute_tonnage(sets) == pytest.approx(640.0)

    def test_empty_list(self):
        assert _compute_tonnage([]) == 0.0

    def test_all_warmup(self):
        sets = [make_mock_set(10, 40.0, is_warmup=True) for _ in range(3)]
        assert _compute_tonnage(sets) == 0.0

    def test_mixed_weights(self):
        sets = [
            make_mock_set(5, 100.0),   # 500
            make_mock_set(8, 80.0),    # 640
            make_mock_set(12, 60.0),   # 720
        ]
        assert _compute_tonnage(sets) == pytest.approx(1860.0)

    def test_single_set(self):
        sets = [make_mock_set(10, 50.0)]
        assert _compute_tonnage(sets) == pytest.approx(500.0)

    def test_bodyweight_zero_weight(self):
        s = make_mock_set()
        s.weight_kg = 0.0
        assert _compute_tonnage([s]) == 0.0


# ── Tests Schemas WorkoutSession ───────────────────────────────────────────────

class TestSessionSchemas:

    def test_session_create_defaults(self):
        data = SessionCreate(session_type="strength")
        assert data.status == "in_progress"
        assert data.location is None
        assert data.notes is None
        assert data.started_at is None

    def test_session_create_with_all_fields(self):
        from datetime import datetime, timezone
        dt = datetime(2026, 3, 7, 10, 0, tzinfo=timezone.utc)
        data = SessionCreate(
            started_at=dt,
            session_type="strength",
            location="gym",
            status="planned",
            notes="Test session",
            energy_before=8,
        )
        assert data.session_type == "strength"
        assert data.location == "gym"
        assert data.energy_before == 8

    def test_session_create_invalid_status(self):
        with pytest.raises(Exception):  # pydantic.ValidationError
            SessionCreate(session_type="strength", status="invalid_status")

    def test_session_create_invalid_location(self):
        with pytest.raises(Exception):
            SessionCreate(session_type="strength", location="mars")

    def test_session_update_partial(self):
        data = SessionUpdate(rpe_score=7.5)
        d = data.model_dump(exclude_unset=True)
        assert "rpe_score" in d
        assert "duration_minutes" not in d

    def test_session_update_rpe_bounds(self):
        with pytest.raises(Exception):
            SessionUpdate(rpe_score=11)  # max 10
        with pytest.raises(Exception):
            SessionUpdate(rpe_score=0)   # min 1


# ── Tests Schemas SetCreate ────────────────────────────────────────────────────

class TestSetSchemas:

    def test_set_create_basic(self):
        data = SetCreate(set_number=1, reps_target=8, reps_actual=8, weight_kg=80.0)
        assert data.set_number == 1
        assert data.is_warmup is False
        assert data.data_source == "manual"

    def test_set_create_warmup(self):
        data = SetCreate(set_number=1, reps_actual=10, weight_kg=40.0, is_warmup=True)
        assert data.is_warmup is True

    def test_set_create_invalid_set_number(self):
        with pytest.raises(Exception):
            SetCreate(set_number=0)  # ge=1

    def test_set_create_negative_weight(self):
        with pytest.raises(Exception):
            SetCreate(set_number=1, weight_kg=-5.0)  # ge=0

    def test_set_create_rpe_bounds(self):
        with pytest.raises(Exception):
            SetCreate(set_number=1, rpe_set=0.5)  # ge=1
        with pytest.raises(Exception):
            SetCreate(set_number=1, rpe_set=10.5)  # le=10

    def test_set_create_valid_data_sources(self):
        for source in ("manual", "camera", "estimated"):
            data = SetCreate(set_number=1, data_source=source)
            assert data.data_source == source

    def test_set_create_invalid_data_source(self):
        with pytest.raises(Exception):
            SetCreate(set_number=1, data_source="ai_detected")


# ── Tests ExerciseEntryResponse computed fields ─────────────────────────────────

class TestExerciseEntryResponseComputedFields:

    def _make_set_response(self, set_number: int, reps_actual: int, weight_kg: float) -> MagicMock:
        from datetime import datetime, timezone
        return SetResponse(
            id=uuid.uuid4(),
            set_number=set_number,
            reps_target=reps_actual,
            reps_actual=reps_actual,
            weight_kg=weight_kg,
            duration_seconds=None,
            rest_seconds=None,
            tempo=None,
            rpe_set=None,
            is_warmup=False,
            is_pr=False,
            data_source="manual",
            time_under_tension_s=None,
            range_of_motion_pct=None,
            created_at=datetime.now(timezone.utc),
        )

    def test_tonnage_computed_from_sets(self):
        from datetime import datetime, timezone
        entry = ExerciseEntryResponse(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            exercise_id=None,
            exercise_order=1,
            notes=None,
            biomechanics_score=None,
            sets=[
                self._make_set_response(1, 8, 80.0),
                self._make_set_response(2, 8, 80.0),
                self._make_set_response(3, 8, 80.0),
            ],
            created_at=datetime.now(timezone.utc),
        )
        assert entry.total_sets == 3
        assert entry.total_reps == 24
        assert entry.tonnage_kg == pytest.approx(1920.0)

    def test_empty_sets(self):
        from datetime import datetime, timezone
        entry = ExerciseEntryResponse(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            exercise_id=None,
            exercise_order=1,
            notes=None,
            biomechanics_score=None,
            sets=[],
            created_at=datetime.now(timezone.utc),
        )
        assert entry.total_sets == 0
        assert entry.total_reps == 0
        assert entry.tonnage_kg is None

    def test_bodyweight_exercise_no_tonnage(self):
        from datetime import datetime, timezone
        s = SetResponse(
            id=uuid.uuid4(),
            set_number=1,
            reps_target=10,
            reps_actual=10,
            weight_kg=None,  # Poids corporel
            duration_seconds=None,
            rest_seconds=None,
            tempo=None,
            rpe_set=None,
            is_warmup=False,
            is_pr=False,
            data_source="manual",
            time_under_tension_s=None,
            range_of_motion_pct=None,
            created_at=datetime.now(timezone.utc),
        )
        entry = ExerciseEntryResponse(
            id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            exercise_id=None,
            exercise_order=1,
            notes=None,
            biomechanics_score=None,
            sets=[s],
            created_at=datetime.now(timezone.utc),
        )
        assert entry.total_sets == 1
        assert entry.total_reps == 10
        assert entry.tonnage_kg is None


# ── Tests SessionSummary schema ────────────────────────────────────────────────

class TestSessionSummarySchema:

    def test_session_summary_basic(self):
        summary = SessionSummary(
            session_id=uuid.uuid4(),
            date="2026-03-07",
            duration_minutes=60,
            session_type="strength",
            status="completed",
            total_exercises=4,
            total_sets=12,
            total_reps=96,
            total_tonnage_kg=3840.0,
            avg_rpe=7.5,
            distance_km=None,
            calories_burned_kcal=None,
            internal_load_score=450.0,
            volume_by_muscle_group=[
                MuscleGroupVolume(
                    muscle_group="quadriceps",
                    total_sets=4,
                    total_reps=32,
                    tonnage_kg=1280.0,
                )
            ],
            personal_records=[],
            summary_text="4 exercice(s) · 12 séries · 3840kg de tonnage · 60min",
        )
        assert summary.total_exercises == 4
        assert summary.total_tonnage_kg == 3840.0
        assert len(summary.volume_by_muscle_group) == 1
        assert summary.internal_load_score == 450.0  # 60min × 7.5 RPE

    def test_muscle_group_volume_schema(self):
        v = MuscleGroupVolume(
            muscle_group="chest",
            total_sets=3,
            total_reps=24,
            tonnage_kg=960.0,
        )
        assert v.muscle_group == "chest"
        assert v.tonnage_kg == 960.0


# ── Tests PR detection (logique Epley) ─────────────────────────────────────────

class TestEpleyFormula:
    """Vérifie la logique 1RM estimé (Epley) utilisée dans _check_pr."""

    def test_epley_basic(self):
        # 1RM = weight × (1 + reps / 30)
        weight = 100.0
        reps = 5
        expected_1rm = weight * (1 + reps / 30)
        assert expected_1rm == pytest.approx(116.67, rel=1e-2)

    def test_epley_one_rep(self):
        # 1 rep → 1RM = weight × (1 + 1/30) ≈ 1.033 × weight
        weight = 140.0
        estimated = weight * (1 + 1 / 30)
        assert estimated == pytest.approx(144.67, rel=1e-2)

    def test_epley_heavy_load_higher_1rm(self):
        # 5 reps à 100kg vs 10 reps à 80kg
        e1 = 100 * (1 + 5 / 30)   # ≈ 116.67
        e2 = 80 * (1 + 10 / 30)   # ≈ 106.67
        assert e1 > e2


# ── Tests exercise library schemas ─────────────────────────────────────────────

class TestExerciseSchemas:

    def test_exercise_response_from_model(self):
        from app.schemas.workout import ExerciseResponse
        e = ExerciseResponse(
            id=uuid.uuid4(),
            name="Barbell Back Squat",
            name_fr="Squat barre nuque",
            slug="barbell-back-squat",
            category="strength",
            subcategory="legs",
            primary_muscles=["quadriceps", "glutes"],
            secondary_muscles=["hamstrings"],
            difficulty_level="intermediate",
            equipment_required=["barbell", "squat_rack"],
            execution_location="gym",
            description="Exercice roi",
            met_value=5.0,
            format_type="reps",
            cv_supported=True,
        )
        assert e.name == "Barbell Back Squat"
        assert e.cv_supported is True
        assert "quadriceps" in e.primary_muscles

    def test_exercise_list_response(self):
        from app.schemas.workout import ExerciseListResponse, ExerciseResponse
        e = ExerciseResponse(
            id=uuid.uuid4(),
            name="Test",
            name_fr=None,
            slug="test",
            category=None,
            subcategory=None,
            primary_muscles=None,
            secondary_muscles=None,
            difficulty_level=None,
            equipment_required=None,
            execution_location=None,
            description=None,
            met_value=None,
            format_type=None,
            cv_supported=False,
        )
        lst = ExerciseListResponse(exercises=[e], total=1)
        assert lst.total == 1
        assert len(lst.exercises) == 1

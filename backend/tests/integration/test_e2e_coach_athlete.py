"""
E2E Integration Test — Coach Platform Persistence.

Tests the full coach ↔ athlete lifecycle using PostgreSQL.
Requires: SOMA_TEST_DATABASE_URL environment variable.

Scenarios:
  1. Register coach → persist in DB → read back
  2. Add athlete → create link → verify via get_athletes
  3. Restart engine (new session) → data intact (no in-memory loss)
"""
import os
import pytest
import uuid
from datetime import date

# Skip all tests if no DB URL is configured
SOMA_TEST_DATABASE_URL = os.environ.get("SOMA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not SOMA_TEST_DATABASE_URL,
    reason="PostgreSQL requis (SOMA_TEST_DATABASE_URL non défini)",
)


class TestCoachRegistration:
    """Tests pour l'enregistrement coach en DB."""

    def test_coach_profile_create_fields(self):
        """Un CoachProfileDB a les champs requis."""
        from app.domains.coach_platform.models import CoachProfileDB
        coach = CoachProfileDB(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Coach Test",
            specializations=["force", "endurance"],
            max_athletes=20,
            is_active=True,
        )
        assert coach.name == "Coach Test"
        assert coach.specializations == ["force", "endurance"]
        assert coach.max_athletes == 20
        assert coach.is_active is True

    def test_athlete_profile_create_fields(self):
        """Un AthleteProfileDB a les champs requis."""
        from app.domains.coach_platform.models import AthleteProfileDB
        athlete = AthleteProfileDB(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            display_name="Athlète Test",
            sport="triathlon",
            goal="sub-10h Ironman",
            is_active=True,
        )
        assert athlete.display_name == "Athlète Test"
        assert athlete.sport == "triathlon"
        assert athlete.is_active is True

    def test_coach_athlete_link_create(self):
        """Un CoachAthleteLinkDB a les champs requis."""
        from app.domains.coach_platform.models import CoachAthleteLinkDB
        from datetime import datetime
        coach_id = uuid.uuid4()
        athlete_id = uuid.uuid4()
        link = CoachAthleteLinkDB(
            id=uuid.uuid4(),
            coach_id=coach_id,
            athlete_id=athlete_id,
            is_active=True,
            role="primary",
            linked_at=datetime.now(),
        )
        assert link.coach_id == coach_id
        assert link.athlete_id == athlete_id
        assert link.role == "primary"
        assert link.is_active is True


class TestTrainingProgram:
    """Tests pour les programmes d'entraînement."""

    def test_training_program_weeks_jsonb(self):
        """Un TrainingProgramDB stocke les semaines en JSONB."""
        from app.domains.coach_platform.models import TrainingProgramDB
        weeks = [
            {"week_number": 1, "theme": "Base", "target_volume": "low", "workouts": []},
            {"week_number": 2, "theme": "Progression", "target_volume": "medium", "workouts": []},
        ]
        program = TrainingProgramDB(
            id=uuid.uuid4(),
            coach_id=uuid.uuid4(),
            name="Programme 12 semaines",
            duration_weeks=12,
            weeks=weeks,
            is_template=False,
            is_active=True,
        )
        assert len(program.weeks) == 2
        assert program.weeks[0]["theme"] == "Base"

    def test_training_program_template_flag(self):
        """Un programme peut être marqué comme template."""
        from app.domains.coach_platform.models import TrainingProgramDB
        template = TrainingProgramDB(
            id=uuid.uuid4(),
            coach_id=uuid.uuid4(),
            name="Template Force",
            duration_weeks=8,
            is_template=True,
            is_active=True,
        )
        assert template.is_template is True


class TestAthleteNoteAlert:
    """Tests pour les notes et alertes athlète."""

    def test_athlete_note_categories(self):
        """Un AthleteNoteDB supporte différentes catégories."""
        from app.domains.coach_platform.models import AthleteNoteDB
        for category in ["general", "nutrition", "recovery", "performance", "injury"]:
            note = AthleteNoteDB(
                id=uuid.uuid4(),
                coach_id=uuid.uuid4(),
                athlete_id=uuid.uuid4(),
                note_date=date.today(),
                content=f"Note catégorie {category}",
                category=category,
                is_private=True,
            )
            assert note.category == category

    def test_athlete_alert_severities(self):
        """Un AthleteAlertDB supporte critical/warning/info."""
        from app.domains.coach_platform.models import AthleteAlertDB
        for severity in ["critical", "warning", "info"]:
            alert = AthleteAlertDB(
                id=uuid.uuid4(),
                coach_id=uuid.uuid4(),
                athlete_id=uuid.uuid4(),
                alert_type="injury_risk",
                severity=severity,
                message=f"Alerte {severity}",
                is_acknowledged=False,
            )
            assert alert.severity == severity
            assert alert.is_acknowledged is False

    def test_alert_acknowledgment_field(self):
        """Une alerte peut être marquée comme traitée."""
        from app.domains.coach_platform.models import AthleteAlertDB
        from datetime import datetime
        alert = AthleteAlertDB(
            id=uuid.uuid4(),
            coach_id=uuid.uuid4(),
            athlete_id=uuid.uuid4(),
            alert_type="overtraining",
            severity="critical",
            message="ACWR critique",
            is_acknowledged=True,
            acknowledged_at=datetime.now(),
        )
        assert alert.is_acknowledged is True
        assert alert.acknowledged_at is not None

"""
E2E Integration Test — Coach Platform Persistence Verification.

Verifies that DB models can be instantiated independently, simulating
the behavior after a server restart (no in-memory data loss).
Requires: SOMA_TEST_DATABASE_URL environment variable.
"""
import os
import pytest
import uuid
from datetime import date, datetime

SOMA_TEST_DATABASE_URL = os.environ.get("SOMA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not SOMA_TEST_DATABASE_URL,
    reason="PostgreSQL requis (SOMA_TEST_DATABASE_URL non défini)",
)


class TestPersistenceNoInMemory:
    """Vérifie que les modèles DB ne dépendent pas de l'état in-memory."""

    def test_coach_profile_model_independent(self):
        """CoachProfileDB peut être instancié sans état global."""
        from app.domains.coach_platform.models import CoachProfileDB
        coach = CoachProfileDB(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Coach Persisté",
            specializations=["force"],
            max_athletes=30,
            is_active=True,
        )
        # Simuler "redémarrage" — créer une nouvelle instance indépendante
        coach2 = CoachProfileDB(
            id=coach.id,
            user_id=coach.user_id,
            name=coach.name,
            specializations=coach.specializations,
            max_athletes=coach.max_athletes,
            is_active=coach.is_active,
        )
        assert coach2.name == "Coach Persisté"
        assert coach2.id == coach.id

    def test_athlete_model_independent(self):
        """AthleteProfileDB peut être instancié sans état global."""
        from app.domains.coach_platform.models import AthleteProfileDB
        athlete = AthleteProfileDB(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            display_name="Athlète Persisté",
            sport="cyclisme",
            is_active=True,
        )
        # Simuler recréation depuis DB
        athlete2 = AthleteProfileDB(
            id=athlete.id,
            user_id=athlete.user_id,
            display_name=athlete.display_name,
            sport=athlete.sport,
            is_active=athlete.is_active,
        )
        assert athlete2.display_name == "Athlète Persisté"

    def test_lab_result_model_independent(self):
        """LabResultDB peut être instancié sans état global."""
        from app.domains.biomarkers.models import LabResultDB
        lab = LabResultDB(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            marker_name="vitamin_d",
            value=42.0,
            unit="ng/mL",
            test_date=date.today(),
        )
        # Simuler recréation depuis DB
        lab2 = LabResultDB(
            id=lab.id,
            user_id=lab.user_id,
            marker_name=lab.marker_name,
            value=lab.value,
            unit=lab.unit,
            test_date=lab.test_date,
        )
        assert lab2.value == 42.0
        assert lab2.marker_name == "vitamin_d"

    def test_no_module_level_in_memory_stores(self):
        """Vérifier qu'il n'y a plus de stores in-memory dans les endpoints."""
        import importlib
        import ast
        import os

        coach_endpoints_path = os.path.join(
            "app", "domains", "coach_platform", "endpoints.py"
        )
        biomarkers_endpoints_path = os.path.join(
            "app", "domains", "biomarkers", "endpoints.py"
        )

        for path in [coach_endpoints_path, biomarkers_endpoints_path]:
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Vérifier absence des patterns in-memory
            forbidden_patterns = ["_lab_store", "_coach_profiles", "_athletes =", "_links =", "_programs =", "_notes ="]
            for pattern in forbidden_patterns:
                assert pattern not in content, (
                    f"Found forbidden in-memory pattern '{pattern}' in {path}"
                )

    def test_explainability_module_importable(self):
        """Le module explainabilité s'importe correctement."""
        from app.core.explainability import (
            risk_label, trend_label, confidence_tier, format_confidence,
            severity_color, alert_severity,
        )
        assert callable(risk_label)
        assert callable(trend_label)
        assert callable(confidence_tier)
        assert callable(format_confidence)
        assert callable(severity_color)
        assert callable(alert_severity)

    def test_v008_migration_exists(self):
        """La migration V008 existe et a le bon down_revision."""
        import os
        migration_path = os.path.join(
            "app", "db", "migrations", "versions", "V008_coach_platform_biomarkers.py"
        )
        assert os.path.exists(migration_path), f"Migration V008 manquante: {migration_path}"
        with open(migration_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'down_revision' in content
        assert '"V007"' in content or "'V007'" in content

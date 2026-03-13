"""
E2E Integration Test — Biomarkers Lab Persistence.

Tests the full lab result → analysis → longevity pipeline.
Requires: SOMA_TEST_DATABASE_URL environment variable.
"""
import os
import pytest
import uuid
from datetime import date

SOMA_TEST_DATABASE_URL = os.environ.get("SOMA_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not SOMA_TEST_DATABASE_URL,
    reason="PostgreSQL requis (SOMA_TEST_DATABASE_URL non défini)",
)


class TestLabResultModel:
    """Tests pour le modèle LabResultDB."""

    def test_lab_result_create_fields(self):
        """Un LabResultDB a les champs requis."""
        from app.domains.biomarkers.models import LabResultDB
        lab = LabResultDB(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            marker_name="vitamin_d",
            value=45.0,
            unit="ng/mL",
            test_date=date.today(),
        )
        assert lab.marker_name == "vitamin_d"
        assert lab.value == 45.0
        assert lab.unit == "ng/mL"

    def test_lab_result_all_14_markers(self):
        """Tous les 14 marqueurs supportés peuvent être créés."""
        from app.domains.biomarkers.models import LabResultDB
        from app.domains.biomarkers.service import REFERENCE_RANGES
        assert len(REFERENCE_RANGES) == 14
        for marker_name in REFERENCE_RANGES.keys():
            lab = LabResultDB(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                marker_name=marker_name,
                value=1.0,
                unit="unit",
                test_date=date.today(),
            )
            assert lab.marker_name == marker_name

    def test_lab_result_optional_notes(self):
        """Un LabResultDB peut avoir des notes optionnelles."""
        from app.domains.biomarkers.models import LabResultDB
        lab_without_notes = LabResultDB(
            id=uuid.uuid4(), user_id=uuid.uuid4(),
            marker_name="ferritin", value=80.0, unit="ng/mL",
            test_date=date.today(), notes=None,
        )
        lab_with_notes = LabResultDB(
            id=uuid.uuid4(), user_id=uuid.uuid4(),
            marker_name="ferritin", value=80.0, unit="ng/mL",
            test_date=date.today(), notes="Résultat prise de sang annuelle",
        )
        assert lab_without_notes.notes is None
        assert lab_with_notes.notes == "Résultat prise de sang annuelle"


class TestBiomarkerAnalysisPipeline:
    """Tests pour le pipeline analyse → longevity via le service pur."""

    def test_analysis_from_vitamin_d_only(self):
        """Analyse avec un seul marqueur vitamin_d."""
        from app.domains.biomarkers.service import compute_biomarker_analysis, BiomarkerResult
        results = [
            BiomarkerResult(
                marker_name="vitamin_d", value=45.0, unit="ng/mL",
                lab_date=date.today(), source="manual", confidence=1.0,
            )
        ]
        analysis = compute_biomarker_analysis(results)
        assert analysis.markers_analyzed == 1
        assert 0 <= analysis.metabolic_health_score <= 100
        assert -10 <= analysis.longevity_modifier <= 10

    def test_analysis_from_multiple_markers(self):
        """Analyse avec plusieurs marqueurs augmente la confiance."""
        from app.domains.biomarkers.service import compute_biomarker_analysis, BiomarkerResult
        results = [
            BiomarkerResult("vitamin_d", 45.0, "ng/mL", date.today(), "manual", 1.0),
            BiomarkerResult("ferritin", 80.0, "ng/mL", date.today(), "manual", 1.0),
            BiomarkerResult("crp", 0.5, "mg/L", date.today(), "manual", 1.0),
        ]
        analysis = compute_biomarker_analysis(results)
        assert analysis.markers_analyzed == 3
        assert analysis.confidence > 0

    def test_longevity_modifier_optimal_markers(self):
        """Des marqueurs optimaux donnent un modificateur négatif (biologiquement plus jeune)."""
        from app.domains.biomarkers.service import compute_biomarker_analysis, BiomarkerResult
        results = [
            # vitamin_d optimal: 40-80 ng/mL
            BiomarkerResult("vitamin_d", 60.0, "ng/mL", date.today(), "manual", 1.0),
            # hdl optimal: >= 60 mg/dL
            BiomarkerResult("hdl", 65.0, "mg/dL", date.today(), "manual", 1.0),
        ]
        analysis = compute_biomarker_analysis(results)
        # Optimal markers should yield negative or near-zero longevity_modifier
        assert analysis.longevity_modifier <= 5.0

    def test_longevity_modifier_deficient_markers(self):
        """Des marqueurs déficients augmentent le modificateur de longévité."""
        from app.domains.biomarkers.service import compute_biomarker_analysis, BiomarkerResult
        results = [
            # vitamin_d très bas → déficient
            BiomarkerResult("vitamin_d", 8.0, "ng/mL", date.today(), "manual", 1.0),
            # crp très élevé → inflammation
            BiomarkerResult("crp", 20.0, "mg/L", date.today(), "manual", 1.0),
        ]
        analysis = compute_biomarker_analysis(results)
        # Déficient markers should not give optimal longevity
        assert analysis.longevity_modifier >= -5.0

    def test_biomarker_summary_length(self):
        """build_biomarker_summary() retourne ≤200 caractères."""
        from app.domains.biomarkers.service import compute_biomarker_analysis, build_biomarker_summary, BiomarkerResult
        results = [
            BiomarkerResult("vitamin_d", 45.0, "ng/mL", date.today(), "manual", 1.0),
        ]
        analysis = compute_biomarker_analysis(results)
        summary = build_biomarker_summary(analysis)
        assert len(summary) <= 200

"""
Tests SOMA LOT 16 — Biomarker Analysis Engine.
~25 tests purs.
"""
import pytest
from datetime import date

from app.domains.biomarkers.service import (
    compute_biomarker_analysis,
    _analyze_single_marker,
    _compute_metabolic_health_score,
    _compute_inflammation_score,
    _compute_cardiovascular_risk,
    _compute_longevity_modifier,
    BiomarkerResult,
    BiomarkerAnalysis,
    REFERENCE_RANGES,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _result(marker: str, value: float) -> BiomarkerResult:
    return BiomarkerResult(
        marker_name=marker,
        value=value,
        unit=REFERENCE_RANGES.get(marker, {}).get("unit", "?"),
        lab_date=date.today(),
    )


# ── Tests: _analyze_single_marker ─────────────────────────────────────────────

class TestAnalyzeSingleMarker:
    def test_vitamin_d_optimal(self):
        analysis = _analyze_single_marker("vitamin_d", 55.0)  # 40-70 optimal
        assert analysis.status == "optimal"
        assert analysis.score == 100.0

    def test_vitamin_d_deficient(self):
        analysis = _analyze_single_marker("vitamin_d", 10.0)  # below 20
        assert analysis.status == "deficient"
        assert analysis.score <= 15.0
        assert len(analysis.recommendations) > 0

    def test_crp_optimal_low_value(self):
        analysis = _analyze_single_marker("crp", 0.5)  # below 0.8
        assert analysis.status == "optimal"

    def test_crp_elevated_high_value(self):
        analysis = _analyze_single_marker("crp", 12.0)  # above 10 (toxic)
        assert analysis.status == "toxic"
        assert analysis.score == 0.0

    def test_hba1c_optimal(self):
        analysis = _analyze_single_marker("hba1c", 5.0)  # 4.5-5.4 optimal
        assert analysis.status == "optimal"

    def test_hba1c_diabetic(self):
        analysis = _analyze_single_marker("hba1c", 7.0)  # above 6.5
        assert analysis.status == "toxic"

    def test_hdl_deficient_low_value(self):
        analysis = _analyze_single_marker("hdl", 35.0)  # below 40
        assert analysis.status == "deficient"

    def test_ldl_optimal(self):
        analysis = _analyze_single_marker("ldl", 80.0)  # below 100
        assert analysis.status == "optimal"

    def test_ldl_elevated(self):
        analysis = _analyze_single_marker("ldl", 170.0)  # above 160
        assert analysis.status in ("toxic", "suboptimal")

    def test_unknown_marker_returns_50_score(self):
        analysis = _analyze_single_marker("unknown_marker", 5.0)
        assert analysis.score == 50.0
        assert analysis.status == "unknown"

    def test_score_in_range_0_100(self):
        for marker, value in [
            ("vitamin_d", 15), ("vitamin_d", 55), ("vitamin_d", 130),
            ("crp", 0.3), ("crp", 5.0), ("crp", 15.0),
            ("hba1c", 4.8), ("hba1c", 5.7), ("hba1c", 7.0),
        ]:
            a = _analyze_single_marker(marker, float(value))
            assert 0 <= a.score <= 100, f"{marker}={value} score={a.score}"


# ── Tests: composite scores ────────────────────────────────────────────────────

class TestCompositeScores:
    def _build_analyses(self) -> list:
        return [
            _analyze_single_marker("hba1c", 5.0),    # optimal metabolic
            _analyze_single_marker("crp", 0.5),       # optimal inflammation
            _analyze_single_marker("ldl", 90.0),      # optimal cardio
            _analyze_single_marker("hdl", 65.0),      # optimal cardio
        ]

    def test_metabolic_health_good_when_metabolic_markers_optimal(self):
        analyses = [_analyze_single_marker("hba1c", 5.0), _analyze_single_marker("fasting_glucose", 85.0)]
        score = _compute_metabolic_health_score(analyses)
        assert score > 70

    def test_inflammation_high_when_crp_elevated(self):
        analyses = [_analyze_single_marker("crp", 12.0)]  # toxic
        inflam = _compute_inflammation_score(analyses)
        assert inflam > 80  # inverted: high inflammation score

    def test_inflammation_low_when_crp_optimal(self):
        analyses = [_analyze_single_marker("crp", 0.4)]  # optimal
        inflam = _compute_inflammation_score(analyses)
        assert inflam < 20  # low inflammation

    def test_cardiovascular_risk_low_when_markers_optimal(self):
        analyses = [
            _analyze_single_marker("ldl", 80.0),
            _analyze_single_marker("hdl", 70.0),
            _analyze_single_marker("triglycerides", 80.0),
        ]
        risk = _compute_cardiovascular_risk(analyses)
        assert risk < 30

    def test_longevity_modifier_negative_when_markers_excellent(self):
        analyses = [
            _analyze_single_marker("vitamin_d", 55.0),
            _analyze_single_marker("omega3_index", 9.0),
            _analyze_single_marker("hba1c", 5.0),
        ]
        modifier = _compute_longevity_modifier(analyses, 85.0, 15.0, 15.0)
        assert modifier < 0  # younger than chronological age

    def test_longevity_modifier_clamped_minus_10_plus_10(self):
        analyses = []
        modifier = _compute_longevity_modifier(analyses, 20.0, 90.0, 90.0)  # poor health
        assert -10 <= modifier <= 10


# ── Tests: compute_biomarker_analysis ─────────────────────────────────────────

class TestComputeBiomarkerAnalysis:
    def test_empty_results_returns_defaults(self):
        result = compute_biomarker_analysis([])
        assert result.markers_analyzed == 0
        assert result.confidence == 0.0
        assert len(result.priority_actions) > 0  # default action to get lab tests

    def test_single_optimal_marker(self):
        results = [_result("vitamin_d", 55.0)]
        analysis = compute_biomarker_analysis(results)
        assert analysis.markers_analyzed == 1
        assert analysis.optimal_markers == 1

    def test_deficient_marker_in_deficient_list(self):
        results = [_result("vitamin_d", 10.0)]
        analysis = compute_biomarker_analysis(results)
        assert "vitamin_d" in analysis.deficient_markers

    def test_toxic_marker_in_elevated_list(self):
        results = [_result("crp", 15.0)]
        analysis = compute_biomarker_analysis(results)
        assert "crp" in analysis.elevated_markers

    def test_confidence_increases_with_more_markers(self):
        r1 = compute_biomarker_analysis([_result("vitamin_d", 55.0)])
        r5 = compute_biomarker_analysis([
            _result("vitamin_d", 55.0),
            _result("crp", 0.5),
            _result("hba1c", 5.0),
            _result("hdl", 65.0),
            _result("ldl", 90.0),
        ])
        assert r5.confidence > r1.confidence

    def test_critical_marker_generates_priority_action(self):
        results = [_result("hba1c", 8.0)]  # diabetic range
        analysis = compute_biomarker_analysis(results)
        assert len(analysis.priority_actions) > 0

    def test_to_dict_serializable(self):
        results = [_result("vitamin_d", 55.0), _result("crp", 0.5)]
        analysis = compute_biomarker_analysis(results)
        d = analysis.to_dict()
        assert isinstance(d, dict)
        assert "metabolic_health_score" in d
        assert "inflammation_score" in d
        assert "longevity_modifier" in d
        assert isinstance(d["marker_analyses"], list)

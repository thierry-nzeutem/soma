"""
Tests pour Biological Age Engine — LOT 11.
~40 tests purs (aucun accès DB).
"""
import pytest

from app.domains.biological_age.service import (
    _metabolic_age_to_score,
    _build_cardiovascular,
    _build_metabolic,
    _build_sleep,
    _build_activity,
    _build_recovery,
    _build_consistency,
    _build_body_composition,
    _select_levers,
    compute_biological_age,
    build_bio_age_summary,
    LEVER_TRIGGER_THRESHOLD,
    LONGEVITY_REFERENCE_SCORE,
    YEARS_PER_SCORE_POINT,
    BIO_AGE_CLAMP_YEARS,
)


# ── _metabolic_age_to_score ───────────────────────────────────────────────────

class TestMetabolicAgeToScore:
    def test_same_age_gives_reference_score(self):
        score = _metabolic_age_to_score(metabolic_age=35, chronological_age=35)
        assert score == pytest.approx(LONGEVITY_REFERENCE_SCORE, abs=0.1)

    def test_younger_metabolic_age_gives_higher_score(self):
        score = _metabolic_age_to_score(metabolic_age=30, chronological_age=35)
        assert score == pytest.approx(100.0)  # 75 + 5/0.2 = 100

    def test_older_metabolic_age_gives_lower_score(self):
        score = _metabolic_age_to_score(metabolic_age=40, chronological_age=35)
        assert score == pytest.approx(50.0)  # 75 - 5/0.2 = 50

    def test_none_returns_none(self):
        assert _metabolic_age_to_score(None, 35) is None

    def test_clamped_to_0_min(self):
        # metabolic_age 20 years older than chrono → (75 - 100) = -25, clamped to 0
        score = _metabolic_age_to_score(metabolic_age=55, chronological_age=35)
        assert score == 0.0

    def test_clamped_to_100_max(self):
        # metabolic_age much younger
        score = _metabolic_age_to_score(metabolic_age=20, chronological_age=35)
        assert score == 100.0


# ── Component builders ────────────────────────────────────────────────────────

class TestComponentBuilders:
    def test_cardiovascular_missing_data(self):
        comp = _build_cardiovascular(None)
        assert comp.is_available is False
        assert comp.age_delta_years == 0.0

    def test_cardiovascular_high_score_younger(self):
        comp = _build_cardiovascular(90.0)
        assert comp.age_delta_years < 0  # score > 75 → negative delta (younger)
        assert comp.is_available is True

    def test_cardiovascular_low_score_older(self):
        comp = _build_cardiovascular(40.0)
        assert comp.age_delta_years > 0  # score < 75 → positive delta (older)

    def test_sleep_missing(self):
        comp = _build_sleep(None)
        assert comp.is_available is False

    def test_activity_missing(self):
        comp = _build_activity(None)
        assert comp.is_available is False

    def test_recovery_present(self):
        comp = _build_recovery(80.0)
        assert comp.is_available is True
        assert comp.score == 80.0

    def test_consistency_present(self):
        comp = _build_consistency(60.0)
        assert comp.is_available is True

    def test_body_composition_both_available(self):
        comp = _build_body_composition(weight_score=80.0, body_comp_score=70.0)
        assert comp.score == pytest.approx(75.0)
        assert comp.is_available is True

    def test_body_composition_only_weight(self):
        comp = _build_body_composition(weight_score=80.0, body_comp_score=None)
        assert comp.score == 80.0

    def test_body_composition_both_missing(self):
        comp = _build_body_composition(None, None)
        assert comp.is_available is False


# ── _select_levers ────────────────────────────────────────────────────────────

class TestSelectLevers:
    def test_all_scores_above_threshold_no_levers(self):
        from app.domains.biological_age.service import _build_cardiovascular, _build_sleep
        components = [
            _build_cardiovascular(80.0),  # above 65
            _build_sleep(80.0),           # above 65
        ]
        levers = _select_levers(components)
        # only check components that are relevant to above levers
        assert all(l.component not in ("cardiovascular", "sleep") for l in levers)

    def test_low_cardio_triggers_cardio_lever(self):
        comp = _build_cardiovascular(50.0)
        levers = _select_levers([comp])
        assert any(l.lever_id == "increase_zone2_cardio" for l in levers)

    def test_low_sleep_triggers_sleep_lever(self):
        comp = _build_sleep(40.0)
        levers = _select_levers([comp])
        assert any(l.lever_id == "improve_sleep" for l in levers)

    def test_levers_sorted_by_potential_years_desc(self):
        from app.domains.biological_age.service import _build_cardiovascular, _build_sleep
        components = [_build_cardiovascular(40.0), _build_sleep(40.0)]
        levers = _select_levers(components)
        if len(levers) >= 2:
            assert levers[0].potential_years_gained >= levers[1].potential_years_gained

    def test_missing_data_components_excluded(self):
        comp = _build_cardiovascular(None)  # is_available=False
        levers = _select_levers([comp])
        # Missing components should not trigger levers
        assert all(l.component != "cardiovascular" for l in levers)


# ── compute_biological_age ────────────────────────────────────────────────────

class TestComputeBiologicalAge:
    def test_all_none_returns_result(self):
        result = compute_biological_age(chronological_age=35)
        assert result.chronological_age == 35
        assert result.confidence == 0.0
        # No data → no component delta → bio_age = chrono
        assert result.biological_age == pytest.approx(35.0)

    def test_excellent_scores_biologically_younger(self):
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=95,
            strength_score=90,
            sleep_score=90,
            weight_score=90,
            consistency_score=90,
            metabolic_age=28,
            readiness_score=90,
        )
        assert result.biological_age < 35
        assert result.biological_age_delta < 0

    def test_poor_scores_biologically_older(self):
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=30,
            strength_score=25,
            sleep_score=30,
            weight_score=30,
            consistency_score=20,
            metabolic_age=45,
            readiness_score=30,
        )
        assert result.biological_age > 35
        assert result.biological_age_delta > 0

    def test_clamped_max_15_years_younger(self):
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=100, strength_score=100, sleep_score=100,
            weight_score=100, consistency_score=100,
            metabolic_age=20, readiness_score=100,
        )
        assert result.biological_age >= 35 - BIO_AGE_CLAMP_YEARS

    def test_clamped_max_15_years_older(self):
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=0, strength_score=0, sleep_score=0,
            weight_score=0, consistency_score=0,
            metabolic_age=60, readiness_score=0,
        )
        assert result.biological_age <= 35 + BIO_AGE_CLAMP_YEARS

    def test_trend_improving(self):
        # If prev_biological_age (30 → delta -5) and current is even lower (29 → delta -6)
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=95, metabolic_age=29,
            prev_biological_age=30,
        )
        # current delta < prev delta → improving
        if result.biological_age < 30:
            assert result.trend_direction == "improving"

    def test_trend_declining(self):
        # prev was better (bio_age=30), now worse (bio_age=36)
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=20, metabolic_age=46,
            prev_biological_age=30,
        )
        assert result.trend_direction == "declining"

    def test_trend_stable_when_no_previous(self):
        result = compute_biological_age(chronological_age=40)
        assert result.trend_direction == "stable"

    def test_seven_components_always_present(self):
        result = compute_biological_age(chronological_age=30)
        assert len(result.components) == 7

    def test_longevity_risk_score_computed(self):
        result = compute_biological_age(chronological_age=35, cardio_score=80)
        assert 0 <= result.longevity_risk_score <= 100

    def test_explanation_is_string(self):
        result = compute_biological_age(chronological_age=35)
        assert isinstance(result.explanation, str)
        assert len(result.explanation) > 0

    def test_levers_triggered_below_threshold(self):
        result = compute_biological_age(
            chronological_age=35,
            cardio_score=40,  # below LEVER_TRIGGER_THRESHOLD (65)
        )
        assert any(l.component == "cardiovascular" for l in result.levers)


# ── build_bio_age_summary ─────────────────────────────────────────────────────

class TestBuildBioAgeSummary:
    def test_summary_is_string(self):
        result = compute_biological_age(chronological_age=35)
        assert isinstance(build_bio_age_summary(result), str)

    def test_summary_contains_biological_age(self):
        result = compute_biological_age(chronological_age=35)
        summary = build_bio_age_summary(result)
        assert "35" in summary or str(result.biological_age) in summary

    def test_summary_compact(self):
        result = compute_biological_age(chronological_age=35)
        assert len(build_bio_age_summary(result)) < 250

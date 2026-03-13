"""
Tests unitaires — Supplement Engine (LOT 3).

Couvre :
  - _suggest_vitamin_d (5 tests)
  - _suggest_magnesium (4 tests)
  - _suggest_creatine (5 tests)
  - _suggest_protein (4 tests)
  - _suggest_iron (4 tests)
  - generate_supplement_recommendations — intégration (7 tests)
  - build_analysis_basis (3 tests)
"""
import pytest
from app.services.supplement_engine import (
    _suggest_vitamin_d,
    _suggest_magnesium,
    _suggest_creatine,
    _suggest_protein,
    _suggest_iron,
    _suggest_zinc,
    generate_supplement_recommendations,
    build_analysis_basis,
)
from app.services.micronutrient_engine import (
    MicronutrientAnalysis,
    MicronutrientResult,
)


# ── Helpers pour construire des MicronutrientAnalysis de test ──────────────────

def _make_micro_result(key: str, pct: float, status: str) -> MicronutrientResult:
    return MicronutrientResult(
        key=key, name=key, name_fr=key, unit="mg",
        consumed=pct, target=100.0,
        pct_of_target=pct, status=status, food_sources=[],
    )


def _make_analysis(results: list, score: float = 60.0) -> MicronutrientAnalysis:
    return MicronutrientAnalysis(
        micronutrients=results,
        overall_micro_score=score,
        top_deficiencies=[r.key for r in results if r.status == "deficient"],
        data_quality="partial",
        entries_with_micro_data_pct=30.0,
        analysis_note="Test analysis",
    )


# ── _suggest_vitamin_d ────────────────────────────────────────────────────────

class TestSuggestVitaminD:

    def test_deficient_triggers_high_confidence(self):
        vd = _make_micro_result("vitamin_d_mcg", 30.0, "deficient")
        analysis = _make_analysis([vd])
        result = _suggest_vitamin_d(analysis)
        assert result is not None
        assert result.confidence_level >= 0.80

    def test_low_triggers_medium_confidence(self):
        vd = _make_micro_result("vitamin_d_mcg", 60.0, "low")
        analysis = _make_analysis([vd])
        result = _suggest_vitamin_d(analysis)
        assert result is not None
        assert result.confidence_level < 0.85

    def test_unknown_triggers_low_confidence(self):
        vd = _make_micro_result("vitamin_d_mcg", 0.0, "unknown")
        analysis = _make_analysis([vd])
        result = _suggest_vitamin_d(analysis)
        assert result is not None
        assert result.confidence_level == 0.50

    def test_sufficient_returns_none(self):
        vd = _make_micro_result("vitamin_d_mcg", 95.0, "sufficient")
        analysis = _make_analysis([vd])
        result = _suggest_vitamin_d(analysis)
        assert result is None

    def test_no_analysis_returns_none(self):
        result = _suggest_vitamin_d(None)
        assert result is None

    def test_result_has_correct_name(self):
        vd = _make_micro_result("vitamin_d_mcg", 20.0, "deficient")
        result = _suggest_vitamin_d(_make_analysis([vd]))
        assert result.supplement_name == "Vitamine D3"


# ── _suggest_magnesium ────────────────────────────────────────────────────────

class TestSuggestMagnesium:

    def test_deficient_with_training_load(self):
        mg = _make_micro_result("magnesium_mg", 40.0, "deficient")
        analysis = _make_analysis([mg])
        result = _suggest_magnesium(analysis, training_load=500)
        assert result is not None

    def test_sufficient_returns_none(self):
        mg = _make_micro_result("magnesium_mg", 90.0, "sufficient")
        analysis = _make_analysis([mg])
        result = _suggest_magnesium(analysis, training_load=500)
        assert result is None

    def test_no_analysis_returns_none(self):
        result = _suggest_magnesium(None, training_load=500)
        assert result is None

    def test_deficient_no_training(self):
        mg = _make_micro_result("magnesium_mg", 30.0, "deficient")
        analysis = _make_analysis([mg])
        result = _suggest_magnesium(analysis, training_load=None)
        assert result is not None  # Suggéré même sans charge d'entraînement


# ── _suggest_creatine ─────────────────────────────────────────────────────────

class TestSuggestCreatine:

    def test_muscle_gain_intermediate(self):
        result = _suggest_creatine("muscle_gain", "intermediate", "strength")
        assert result is not None
        assert result.supplement_name == "Créatine Monohydrate"

    def test_weight_loss_goal_returns_none(self):
        result = _suggest_creatine("weight_loss", "intermediate", "strength")
        assert result is None

    def test_beginner_returns_none(self):
        result = _suggest_creatine("muscle_gain", "beginner", "strength")
        assert result is None

    def test_performance_goal_athlete(self):
        result = _suggest_creatine("performance", "athlete", "mixed")
        assert result is not None

    def test_none_goal_returns_none(self):
        result = _suggest_creatine(None, "intermediate", "strength")
        assert result is None


# ── _suggest_protein ──────────────────────────────────────────────────────────

class TestSuggestProtein:

    def test_below_70pct_triggers_suggestion(self):
        result = _suggest_protein(0.50, "muscle_gain", None)
        assert result is not None

    def test_above_70pct_returns_none(self):
        result = _suggest_protein(0.80, "muscle_gain", None)
        assert result is None

    def test_none_ratio_returns_none(self):
        result = _suggest_protein(None, "muscle_gain", None)
        assert result is None

    def test_vegan_uses_plant_protein(self):
        result = _suggest_protein(0.50, "muscle_gain", "vegan")
        assert result is not None
        assert "végétal" in result.supplement_name.lower() or "végétal" in result.goal.lower()


# ── _suggest_iron ─────────────────────────────────────────────────────────────

class TestSuggestIron:

    def test_deficient_female(self):
        fe = _make_micro_result("iron_mg", 20.0, "deficient")
        analysis = _make_analysis([fe])
        result = _suggest_iron(analysis, "female")
        assert result is not None

    def test_male_returns_none(self):
        fe = _make_micro_result("iron_mg", 20.0, "deficient")
        analysis = _make_analysis([fe])
        result = _suggest_iron(analysis, "male")
        assert result is None

    def test_sufficient_female_returns_none(self):
        fe = _make_micro_result("iron_mg", 90.0, "sufficient")
        analysis = _make_analysis([fe])
        result = _suggest_iron(analysis, "female")
        assert result is None

    def test_no_analysis_returns_none(self):
        result = _suggest_iron(None, "female")
        assert result is None


# ── generate_supplement_recommendations — intégration ─────────────────────────

class TestGenerateSupplementRecommendations:

    def _make_deficient_analysis(self):
        results = [
            _make_micro_result("vitamin_d_mcg", 20.0, "deficient"),
            _make_micro_result("magnesium_mg", 30.0, "deficient"),
            _make_micro_result("potassium_mg", 40.0, "low"),
            _make_micro_result("sodium_mg", 80.0, "sufficient"),
            _make_micro_result("calcium_mg", 50.0, "low"),
            _make_micro_result("iron_mg", 20.0, "deficient"),
            _make_micro_result("zinc_mg", 40.0, "deficient"),
            _make_micro_result("omega3_g", 30.0, "deficient"),
        ]
        return _make_analysis(results, score=35.0)

    def test_returns_max_5_suggestions(self):
        analysis = self._make_deficient_analysis()
        suggestions = generate_supplement_recommendations(
            primary_goal="muscle_gain", fitness_level="intermediate",
            sex="male", micro_analysis=analysis,
        )
        assert len(suggestions) <= 5

    def test_sorted_by_confidence_descending(self):
        analysis = self._make_deficient_analysis()
        suggestions = generate_supplement_recommendations(
            primary_goal="muscle_gain", fitness_level="intermediate",
            sex="male", micro_analysis=analysis,
        )
        for i in range(len(suggestions) - 1):
            assert suggestions[i].confidence_level >= suggestions[i + 1].confidence_level

    def test_empty_suggestions_with_no_issues(self):
        results = [
            _make_micro_result("vitamin_d_mcg", 95.0, "sufficient"),
            _make_micro_result("magnesium_mg", 90.0, "sufficient"),
            _make_micro_result("potassium_mg", 85.0, "sufficient"),
            _make_micro_result("sodium_mg", 90.0, "sufficient"),
            _make_micro_result("calcium_mg", 95.0, "sufficient"),
            _make_micro_result("iron_mg", 90.0, "sufficient"),
            _make_micro_result("zinc_mg", 85.0, "sufficient"),
            _make_micro_result("omega3_g", 90.0, "sufficient"),
        ]
        analysis = _make_analysis(results, score=90.0)
        suggestions = generate_supplement_recommendations(
            primary_goal="maintenance",
            sex="male",
            micro_analysis=analysis,
            protein_ratio=0.90,  # suffisant
        )
        # Avec tout suffisant + maintenance + protéines ok → peu ou pas de suggestions
        assert len(suggestions) <= 2  # Peut avoir créatine si objectif non-maintenance

    def test_no_analysis_still_evaluates_creatine(self):
        suggestions = generate_supplement_recommendations(
            primary_goal="muscle_gain", fitness_level="advanced",
            micro_analysis=None,
        )
        names = [s.supplement_name for s in suggestions]
        assert "Créatine Monohydrate" in names

    def test_protein_suggestion_triggered(self):
        suggestions = generate_supplement_recommendations(
            primary_goal="muscle_gain",
            protein_ratio=0.50,  # < 70%
            micro_analysis=None,
        )
        names = [s.supplement_name for s in suggestions]
        assert any("rotéine" in n or "Whey" in n for n in names)

    def test_confidence_in_range(self):
        analysis = self._make_deficient_analysis()
        suggestions = generate_supplement_recommendations(
            primary_goal="muscle_gain",
            fitness_level="intermediate",
            sex="female",
            micro_analysis=analysis,
        )
        for s in suggestions:
            assert 0.0 <= s.confidence_level <= 1.0

    def test_all_fields_present(self):
        vd = _make_micro_result("vitamin_d_mcg", 10.0, "deficient")
        analysis = _make_analysis([vd])
        suggestions = generate_supplement_recommendations(micro_analysis=analysis)
        for s in suggestions:
            assert s.supplement_name
            assert s.goal
            assert s.reason
            assert s.suggested_dose
            assert s.suggested_timing


# ── build_analysis_basis ──────────────────────────────────────────────────────

class TestBuildAnalysisBasis:

    def test_with_all_params(self):
        vd = _make_micro_result("vitamin_d_mcg", 50.0, "low")
        analysis = _make_analysis([vd], score=55.0)
        basis = build_analysis_basis(analysis, 300.0, "muscle_gain")
        assert "55" in basis
        assert "300" in basis
        assert "muscle_gain" in basis

    def test_no_analysis_uses_profile_fallback(self):
        basis = build_analysis_basis(None, None, None)
        assert len(basis) > 10  # Message par défaut

    def test_with_training_load_only(self):
        basis = build_analysis_basis(None, 500.0, None)
        assert "500" in basis

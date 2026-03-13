"""
Tests unitaires — Micronutrient Engine (LOT 3).

Couvre :
  - get_ajr (3 tests)
  - estimate_from_food_group (5 tests)
  - extract_micros_from_food_item (4 tests)
  - classify_status (4 tests)
  - compute_overall_micro_score (4 tests)
  - analyze_micronutrients (8 tests)
"""
import pytest
from app.services.micronutrient_engine import (
    get_ajr,
    estimate_from_food_group,
    extract_micros_from_food_item,
    classify_status,
    compute_overall_micro_score,
    analyze_micronutrients,
    AJR_MALE,
    AJR_FEMALE,
    MicronutrientResult,
    STATUS_THRESHOLDS,
)


# ── get_ajr ───────────────────────────────────────────────────────────────────

class TestGetAJR:

    def test_male_ajr(self):
        ajr = get_ajr("male")
        assert ajr["iron_mg"] == pytest.approx(8.0)
        assert ajr["zinc_mg"] == pytest.approx(11.0)

    def test_female_ajr(self):
        ajr = get_ajr("female")
        assert ajr["iron_mg"] == pytest.approx(18.0)   # Plus élevé pour les femmes
        assert ajr["zinc_mg"] == pytest.approx(8.0)

    def test_none_sex_returns_male_defaults(self):
        ajr = get_ajr(None)
        assert ajr == AJR_MALE

    def test_other_sex_returns_male_defaults(self):
        ajr = get_ajr("other")
        assert ajr == AJR_MALE

    def test_all_keys_present(self):
        ajr = get_ajr("male")
        expected_keys = {"vitamin_d_mcg", "magnesium_mg", "potassium_mg",
                         "sodium_mg", "calcium_mg", "iron_mg", "zinc_mg", "omega3_g"}
        assert set(ajr.keys()) == expected_keys


# ── estimate_from_food_group ──────────────────────────────────────────────────

class TestEstimateFromFoodGroup:

    def test_none_food_group_returns_empty(self):
        result = estimate_from_food_group(None, 100)
        assert result == {}

    def test_none_quantity_returns_empty(self):
        result = estimate_from_food_group("protein", None)
        assert result == {}

    def test_zero_quantity_returns_empty(self):
        result = estimate_from_food_group("dairy", 0)
        assert result == {}

    def test_protein_group_has_iron(self):
        result = estimate_from_food_group("protein", 100)
        assert "iron_mg" in result
        assert result["iron_mg"] > 0

    def test_scaling_by_quantity(self):
        result_100 = estimate_from_food_group("dairy", 100)
        result_200 = estimate_from_food_group("dairy", 200)
        for key in result_100:
            assert result_200[key] == pytest.approx(result_100[key] * 2, rel=1e-3)

    def test_unknown_group_returns_empty(self):
        result = estimate_from_food_group("mystery_food", 100)
        assert result == {}


# ── extract_micros_from_food_item ─────────────────────────────────────────────

class TestExtractMicrosFromFoodItem:

    def test_none_jsonb_returns_empty(self):
        result = extract_micros_from_food_item(None, 100)
        assert result == {}

    def test_none_quantity_returns_empty(self):
        result = extract_micros_from_food_item({"vitamin_d_mcg": 5.0}, None)
        assert result == {}

    def test_scaling_by_quantity(self):
        jsonb = {"vitamin_d_mcg": 10.0, "iron_mg": 2.0}
        result_50 = extract_micros_from_food_item(jsonb, 50)
        result_100 = extract_micros_from_food_item(jsonb, 100)
        assert result_100["vitamin_d_mcg"] == pytest.approx(10.0, rel=1e-3)
        assert result_50["vitamin_d_mcg"] == pytest.approx(5.0, rel=1e-3)

    def test_unknown_keys_ignored(self):
        jsonb = {"vitamin_d_mcg": 5.0, "unknown_nutrient": 99.0}
        result = extract_micros_from_food_item(jsonb, 100)
        assert "unknown_nutrient" not in result
        assert "vitamin_d_mcg" in result

    def test_zero_quantity_returns_empty(self):
        result = extract_micros_from_food_item({"iron_mg": 5.0}, 0)
        assert result == {}


# ── classify_status ───────────────────────────────────────────────────────────

class TestClassifyStatus:

    def test_none_returns_unknown(self):
        assert classify_status(None) == "unknown"

    def test_above_threshold_sufficient(self):
        assert classify_status(100.0) == "sufficient"
        assert classify_status(80.0) == "sufficient"

    def test_between_thresholds_low(self):
        assert classify_status(60.0) == "low"
        assert classify_status(50.0) == "low"

    def test_below_low_threshold_deficient(self):
        assert classify_status(30.0) == "deficient"
        assert classify_status(0.0) == "deficient"


# ── compute_overall_micro_score ───────────────────────────────────────────────

class TestComputeOverallMicroScore:

    def _make_result(self, pct):
        return MicronutrientResult(
            key="test", name="Test", name_fr="Test", unit="mg",
            consumed=pct, target=100.0,
            pct_of_target=pct, status="sufficient", food_sources=[],
        )

    def test_empty_list_returns_zero(self):
        assert compute_overall_micro_score([]) == 0.0

    def test_all_sufficient_returns_avg(self):
        results = [self._make_result(90.0), self._make_result(80.0)]
        score = compute_overall_micro_score(results)
        assert score == pytest.approx(85.0, abs=0.5)

    def test_capped_at_100(self):
        results = [self._make_result(120.0), self._make_result(150.0)]
        score = compute_overall_micro_score(results)
        assert score <= 100.0

    def test_none_pct_excluded(self):
        r1 = self._make_result(80.0)
        r2 = MicronutrientResult(
            key="x", name="X", name_fr="X", unit="mg",
            consumed=None, target=100.0, pct_of_target=None,
            status="unknown", food_sources=[],
        )
        # r2 sans pct_of_target ne doit pas influencer le score (n=0 pour ce)
        score = compute_overall_micro_score([r1, r2])
        # Seul r1 compte → score = 80
        assert score == pytest.approx(80.0, abs=0.5)


# ── analyze_micronutrients ────────────────────────────────────────────────────

class TestAnalyzeMicronutrients:

    class _Entry:
        """Proxy d'entrée nutritionnelle pour les tests."""
        def __init__(self, quantity_g=None, food_group=None, micro_jsonb=None, calories=None):
            self.quantity_g = quantity_g
            self.food_group = food_group
            self.food_item_micronutrients = micro_jsonb
            self.calories = calories

    def test_empty_entries_returns_zero_score(self):
        result = analyze_micronutrients([], sex="male")
        assert result.overall_micro_score == 0.0

    def test_returns_8_micronutrients(self):
        result = analyze_micronutrients([], sex="male")
        assert len(result.micronutrients) == 8

    def test_protein_food_group_estimates_iron(self):
        entries = [self._Entry(quantity_g=200, food_group="protein")]
        result = analyze_micronutrients(entries, sex="male")
        iron = next(r for r in result.micronutrients if r.key == "iron_mg")
        assert iron.consumed is not None
        assert iron.consumed > 0

    def test_catalog_data_has_good_quality(self):
        micro_jsonb = {
            "vitamin_d_mcg": 15.0, "magnesium_mg": 40.0, "potassium_mg": 400.0,
            "sodium_mg": 100.0, "calcium_mg": 200.0, "iron_mg": 3.0,
            "zinc_mg": 2.0, "omega3_g": 0.5,
        }
        entries = [self._Entry(quantity_g=150, micro_jsonb=micro_jsonb)]
        result = analyze_micronutrients(entries, sex="male")
        assert result.data_quality == "good"
        assert result.entries_with_micro_data_pct == 100.0

    def test_no_catalog_data_is_estimated(self):
        entries = [self._Entry(quantity_g=200, food_group="grain")]
        result = analyze_micronutrients(entries, sex="male")
        assert result.data_quality == "estimated"

    def test_female_ajr_used_for_iron(self):
        # Même entrée, AJR fer différent selon sexe
        micro_jsonb = {"iron_mg": 10.0}
        entries = [self._Entry(quantity_g=100, micro_jsonb=micro_jsonb)]
        result_male = analyze_micronutrients(entries, sex="male")
        result_female = analyze_micronutrients(entries, sex="female")
        iron_male = next(r for r in result_male.micronutrients if r.key == "iron_mg")
        iron_female = next(r for r in result_female.micronutrients if r.key == "iron_mg")
        # Fe homme = 8mg AJR, femme = 18mg → % différent avec 10mg
        assert iron_male.pct_of_target != pytest.approx(iron_female.pct_of_target, abs=1.0)

    def test_top_deficiencies_are_listed(self):
        # Entrée qui donne de très faibles apports
        entries = [self._Entry(quantity_g=10, food_group="protein")]
        result = analyze_micronutrients(entries, sex="male")
        # Avec si peu de nourriture, il devrait y avoir des déficiences
        assert isinstance(result.top_deficiencies, list)

    def test_days_normalization(self):
        micro_jsonb = {
            "vitamin_d_mcg": 20.0, "magnesium_mg": 420.0, "potassium_mg": 3400.0,
            "sodium_mg": 2300.0, "calcium_mg": 1000.0, "iron_mg": 8.0,
            "zinc_mg": 11.0, "omega3_g": 1.6,
        }
        # 7 entrées, analyse sur 7 jours → normalisé = 1 par jour
        entries = [self._Entry(quantity_g=100, micro_jsonb=micro_jsonb) for _ in range(7)]
        result_7d = analyze_micronutrients(entries, sex="male", days=7)
        result_1d = analyze_micronutrients(
            [self._Entry(quantity_g=100, micro_jsonb=micro_jsonb)], sex="male", days=1
        )
        vd_7d = next(r for r in result_7d.micronutrients if r.key == "vitamin_d_mcg")
        vd_1d = next(r for r in result_1d.micronutrients if r.key == "vitamin_d_mcg")
        # Les deux devraient être proches après normalisation
        assert abs((vd_7d.consumed or 0) - (vd_1d.consumed or 0)) < 5.0

"""
Tests unitaires — nutrition_service.py (fonctions pures, sans DB).

Stratégie :
  - Tests sur compute_macros_from_food_item (pure function)
  - Tests sur compute_eating_window (pure function)
  - Tests sur compute_data_completeness (pure function)
  - Tests sur les schémas Pydantic NutritionEntryCreate (validation)
  - Pas de DB requise
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import uuid

from app.services.nutrition_service import (
    compute_macros_from_food_item,
    compute_eating_window,
    compute_data_completeness,
)
from app.schemas.nutrition import (
    NutritionEntryCreate,
    NutritionEntryUpdate,
    FoodItemResponse,
    DailyNutritionSummary,
    MacroActuals,
    EatingWindow,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_mock_food_item(
    calories=400.0, protein=25.0, carbs=50.0, fat=10.0, fiber=5.0
) -> MagicMock:
    """Crée un mock FoodItem pour 100g."""
    item = MagicMock()
    item.calories_per_100g = calories
    item.protein_g_per_100g = protein
    item.carbs_g_per_100g = carbs
    item.fat_g_per_100g = fat
    item.fiber_g_per_100g = fiber
    return item


def make_mock_entry(logged_at: datetime, calories: float = None) -> MagicMock:
    entry = MagicMock()
    entry.logged_at = logged_at
    entry.calories = calories
    return entry


# ── Tests compute_macros_from_food_item ────────────────────────────────────────

class TestComputeMacrosFromFoodItem:

    def test_basic_100g(self):
        item = make_mock_food_item(calories=400, protein=25, carbs=50, fat=10, fiber=5)
        result = compute_macros_from_food_item(item, 100.0)
        assert result["calories"] == pytest.approx(400.0)
        assert result["protein_g"] == pytest.approx(25.0)
        assert result["carbs_g"] == pytest.approx(50.0)
        assert result["fat_g"] == pytest.approx(10.0)
        assert result["fiber_g"] == pytest.approx(5.0)

    def test_half_portion(self):
        item = make_mock_food_item(calories=400, protein=20, carbs=60, fat=8, fiber=4)
        result = compute_macros_from_food_item(item, 50.0)
        assert result["calories"] == pytest.approx(200.0)
        assert result["protein_g"] == pytest.approx(10.0)
        assert result["carbs_g"] == pytest.approx(30.0)

    def test_double_portion(self):
        item = make_mock_food_item(calories=100, protein=10, carbs=15, fat=3, fiber=2)
        result = compute_macros_from_food_item(item, 200.0)
        assert result["calories"] == pytest.approx(200.0)
        assert result["protein_g"] == pytest.approx(20.0)

    def test_none_per_100g_returns_none(self):
        item = MagicMock()
        item.calories_per_100g = None
        item.protein_g_per_100g = 20.0
        item.carbs_g_per_100g = None
        item.fat_g_per_100g = 5.0
        item.fiber_g_per_100g = None
        result = compute_macros_from_food_item(item, 100.0)
        assert result["calories"] is None
        assert result["protein_g"] == pytest.approx(20.0)
        assert result["carbs_g"] is None
        assert result["fat_g"] == pytest.approx(5.0)
        assert result["fiber_g"] is None

    def test_zero_quantity(self):
        item = make_mock_food_item(calories=400, protein=25, carbs=50, fat=10, fiber=5)
        result = compute_macros_from_food_item(item, 0.0)
        assert result["calories"] == pytest.approx(0.0)
        assert result["protein_g"] == pytest.approx(0.0)

    def test_rounding(self):
        item = make_mock_food_item(calories=333.33, protein=11.11, carbs=44.44, fat=7.77, fiber=2.22)
        result = compute_macros_from_food_item(item, 150.0)
        # Vérifier que la valeur est arrondie à 2 décimales
        assert result["calories"] == pytest.approx(499.995, rel=1e-3)
        # Tous les résultats doivent avoir au plus 2 décimales
        for v in result.values():
            if v is not None:
                assert round(v, 2) == v

    def test_non_standard_quantity(self):
        item = make_mock_food_item(calories=200, protein=15, carbs=30, fat=5, fiber=3)
        result = compute_macros_from_food_item(item, 75.0)
        assert result["calories"] == pytest.approx(150.0)
        assert result["protein_g"] == pytest.approx(11.25)
        assert result["carbs_g"] == pytest.approx(22.5)


# ── Tests compute_eating_window ────────────────────────────────────────────────

class TestComputeEatingWindow:

    def _dt(self, hour: int) -> datetime:
        """Helper : datetime d'aujourd'hui à l'heure donnée (UTC)."""
        return datetime(2026, 3, 7, hour, 0, 0, tzinfo=timezone.utc)

    def test_empty_entries_returns_empty_window(self):
        result = compute_eating_window([])
        assert result.first_meal_at is None
        assert result.last_meal_at is None
        assert result.window_hours is None
        assert result.fasting_compatible is None

    def test_single_entry_zero_window(self):
        entry = make_mock_entry(self._dt(8))
        result = compute_eating_window([entry])
        assert result.first_meal_at == self._dt(8)
        assert result.last_meal_at == self._dt(8)
        assert result.window_hours == pytest.approx(0.0)
        # Une seule entrée = pas de fenêtre → fasting_compatible None
        assert result.fasting_compatible is None

    def test_8h_window_fasting_compatible(self):
        # Fenêtre de 8h = exactement compatible jeûne 16:8
        entries = [
            make_mock_entry(self._dt(8)),
            make_mock_entry(self._dt(12)),
            make_mock_entry(self._dt(16)),
        ]
        result = compute_eating_window(entries)
        assert result.first_meal_at == self._dt(8)
        assert result.last_meal_at == self._dt(16)
        assert result.window_hours == pytest.approx(8.0)
        assert result.fasting_compatible is True

    def test_10h_window_not_fasting_compatible(self):
        entries = [
            make_mock_entry(self._dt(7)),
            make_mock_entry(self._dt(17)),
        ]
        result = compute_eating_window(entries)
        assert result.window_hours == pytest.approx(10.0)
        assert result.fasting_compatible is False

    def test_6h_window_fasting_compatible(self):
        entries = [
            make_mock_entry(self._dt(12)),
            make_mock_entry(self._dt(18)),
        ]
        result = compute_eating_window(entries)
        assert result.window_hours == pytest.approx(6.0)
        assert result.fasting_compatible is True

    def test_entries_without_logged_at_filtered(self):
        entry1 = MagicMock()
        entry1.logged_at = None
        entry2 = make_mock_entry(self._dt(10))
        result = compute_eating_window([entry1, entry2])
        # Seule entry2 a un logged_at → fenêtre = 0
        assert result.first_meal_at == self._dt(10)
        assert result.window_hours == pytest.approx(0.0)


# ── Tests compute_data_completeness ───────────────────────────────────────────

class TestComputeDataCompleteness:

    def test_empty_returns_zero(self):
        assert compute_data_completeness([]) == 0.0

    def test_all_with_calories(self):
        entries = [make_mock_entry(datetime.now(timezone.utc), calories=500) for _ in range(3)]
        assert compute_data_completeness(entries) == pytest.approx(100.0)

    def test_none_with_calories(self):
        entries = [make_mock_entry(datetime.now(timezone.utc), calories=None) for _ in range(4)]
        assert compute_data_completeness(entries) == pytest.approx(0.0)

    def test_partial_completeness(self):
        entries = [
            make_mock_entry(datetime.now(timezone.utc), calories=500),
            make_mock_entry(datetime.now(timezone.utc), calories=None),
            make_mock_entry(datetime.now(timezone.utc), calories=300),
            make_mock_entry(datetime.now(timezone.utc), calories=None),
        ]
        assert compute_data_completeness(entries) == pytest.approx(50.0)

    def test_rounding(self):
        entries = [
            make_mock_entry(datetime.now(timezone.utc), calories=100),
            make_mock_entry(datetime.now(timezone.utc), calories=None),
            make_mock_entry(datetime.now(timezone.utc), calories=None),
        ]
        assert compute_data_completeness(entries) == pytest.approx(33.3)


# ── Tests Schémas Pydantic NutritionEntryCreate ────────────────────────────────

class TestNutritionEntryCreateSchema:

    def test_via_food_item_valid(self):
        data = NutritionEntryCreate(
            food_item_id=uuid.uuid4(),
            quantity_g=150.0,
            meal_type="lunch",
        )
        assert data.food_item_id is not None
        assert data.quantity_g == 150.0

    def test_via_macros_direct(self):
        data = NutritionEntryCreate(
            calories=500.0,
            protein_g=30.0,
            carbs_g=60.0,
            fat_g=15.0,
            meal_type="dinner",
        )
        assert data.calories == 500.0
        assert data.food_item_id is None

    def test_via_photo_id_valid(self):
        data = NutritionEntryCreate(
            photo_id=uuid.uuid4(),
            calories=350.0,
            data_quality="ai_analyzed",
        )
        assert data.photo_id is not None

    def test_no_source_no_macros_raises(self):
        with pytest.raises(Exception):  # ValidationError
            NutritionEntryCreate()  # Aucune source ni macro

    def test_invalid_meal_type_raises(self):
        with pytest.raises(Exception):
            NutritionEntryCreate(
                calories=300.0,
                meal_type="supper",  # invalide
            )

    def test_valid_meal_types(self):
        for mt in ("breakfast", "lunch", "dinner", "snack", "supplement", "drink"):
            data = NutritionEntryCreate(calories=100.0, meal_type=mt)
            assert data.meal_type == mt

    def test_invalid_data_quality_raises(self):
        with pytest.raises(Exception):
            NutritionEntryCreate(
                calories=300.0,
                data_quality="rough_estimate",  # invalide
            )

    def test_negative_quantity_raises(self):
        with pytest.raises(Exception):
            NutritionEntryCreate(
                food_item_id=uuid.uuid4(),
                quantity_g=-50.0,
            )

    def test_hunger_before_bounds(self):
        with pytest.raises(Exception):
            NutritionEntryCreate(calories=300.0, hunger_before=0)  # ge=1
        with pytest.raises(Exception):
            NutritionEntryCreate(calories=300.0, hunger_before=11)  # le=10
        data = NutritionEntryCreate(calories=300.0, hunger_before=5)
        assert data.hunger_before == 5

    def test_defaults(self):
        data = NutritionEntryCreate(calories=200.0)
        assert data.fasting_window_broken is False
        assert data.logged_at is None  # Sera défini par le service
        assert data.data_quality is None


# ── Tests Schémas NutritionEntryUpdate ────────────────────────────────────────

class TestNutritionEntryUpdateSchema:

    def test_empty_update(self):
        data = NutritionEntryUpdate()
        d = data.model_dump(exclude_unset=True)
        assert d == {}

    def test_partial_update(self):
        data = NutritionEntryUpdate(calories=450.0, meal_type="snack")
        d = data.model_dump(exclude_unset=True)
        assert "calories" in d
        assert "meal_type" in d
        assert "protein_g" not in d

    def test_valid_update(self):
        data = NutritionEntryUpdate(
            protein_g=35.0,
            notes="Après entraînement",
        )
        assert data.protein_g == 35.0
        assert data.notes == "Après entraînement"


# ── Tests MacroActuals schema ──────────────────────────────────────────────────

class TestMacroActualsSchema:

    def test_defaults_to_zero(self):
        m = MacroActuals()
        assert m.calories == 0.0
        assert m.protein_g == 0.0
        assert m.carbs_g == 0.0
        assert m.fat_g == 0.0
        assert m.fiber_g == 0.0

    def test_full_instantiation(self):
        m = MacroActuals(calories=2000.0, protein_g=150.0, carbs_g=250.0, fat_g=70.0, fiber_g=30.0)
        assert m.calories == 2000.0
        assert m.protein_g == 150.0

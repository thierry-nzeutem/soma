"""
Tests unitaires — vision_service.py et vision_prompt.py (sans API réelle).

Stratégie :
  - Tests sur parse_vision_response (parseur JSON multi-tentatives)
  - Tests sur build_mock_analysis (structure de la réponse mock)
  - Tests sur _populate_photo_from_analysis (logique de mappage)
  - Pas d'appel réseau, pas de DB requise
"""
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
import uuid

from app.utils.vision_prompt import parse_vision_response, build_mock_analysis, MEAL_ANALYSIS_PROMPT
from app.services.vision_service import _populate_photo_from_analysis


# ── Tests build_mock_analysis ──────────────────────────────────────────────────

class TestBuildMockAnalysis:

    def test_returns_dict(self):
        result = build_mock_analysis()
        assert isinstance(result, dict)

    def test_required_keys_present(self):
        result = build_mock_analysis()
        # Le mock doit avoir les clés que parse_vision_response attend
        assert "foods" in result or "estimated_total_calories" in result

    def test_overall_confidence_present(self):
        result = build_mock_analysis()
        assert "overall_confidence" in result
        confidence = result["overall_confidence"]
        assert 0.0 <= confidence <= 1.0

    def test_has_calorie_estimate(self):
        result = build_mock_analysis()
        assert "estimated_total_calories" in result
        assert result["estimated_total_calories"] is not None
        assert result["estimated_total_calories"] > 0

    def test_has_macro_estimates(self):
        result = build_mock_analysis()
        assert "estimated_total_protein_g" in result
        assert "estimated_total_carbs_g" in result
        assert "estimated_total_fat_g" in result

    def test_has_foods_list(self):
        result = build_mock_analysis()
        assert "foods" in result
        assert isinstance(result["foods"], list)
        assert len(result["foods"]) >= 1

    def test_foods_have_required_fields(self):
        result = build_mock_analysis()
        for food in result["foods"]:
            assert "name" in food
            assert "confidence" in food
            assert 0.0 <= food["confidence"] <= 1.0

    def test_deterministic(self):
        """build_mock_analysis doit retourner la même structure à chaque appel."""
        r1 = build_mock_analysis()
        r2 = build_mock_analysis()
        assert r1.keys() == r2.keys()
        assert r1["estimated_total_calories"] == r2["estimated_total_calories"]


# ── Tests parse_vision_response ────────────────────────────────────────────────

class TestParseVisionResponse:

    def _make_valid_json(self, **kwargs) -> str:
        """Génère une réponse JSON valide."""
        base = {
            "foods": [{"name": "Rice", "quantity_g": 100, "confidence": 0.9}],
            "estimated_total_calories": 350,
            "estimated_total_protein_g": 20,
            "estimated_total_carbs_g": 50,
            "estimated_total_fat_g": 8,
            "overall_confidence": 0.85,
            "meal_type_guess": "lunch",
            "warnings": [],
            "assumptions": ["Standard portion"],
            "missing_information": [],
        }
        base.update(kwargs)
        return json.dumps(base)

    def test_direct_json_parsing(self):
        raw = self._make_valid_json()
        result = parse_vision_response(raw)
        assert result["estimated_total_calories"] == 350
        assert result["overall_confidence"] == 0.85

    def test_json_in_markdown_fence(self):
        raw = f"Here is the analysis:\n```json\n{self._make_valid_json()}\n```"
        result = parse_vision_response(raw)
        assert result["estimated_total_calories"] == 350

    def test_json_in_generic_fence(self):
        raw = f"```\n{self._make_valid_json()}\n```"
        result = parse_vision_response(raw)
        assert result["estimated_total_calories"] == 350

    def test_invalid_json_returns_fallback(self):
        """Un JSON invalide retourne un dict vide (pas d'exception)."""
        result = parse_vision_response("This is not JSON at all.")
        assert isinstance(result, dict)
        # La fonction ne doit pas lever d'exception, mais peut retourner un dict vide/partiel

    def test_empty_string_returns_dict(self):
        result = parse_vision_response("")
        assert isinstance(result, dict)

    def test_json_with_extra_text(self):
        """JSON entouré de texte narratif."""
        raw = (
            "I analyzed the image. Here is my response:\n"
            + self._make_valid_json()
            + "\nHope this helps!"
        )
        result = parse_vision_response(raw)
        # Peut réussir ou non selon l'implémentation, mais ne doit pas lever d'exception
        assert isinstance(result, dict)

    def test_confidence_values_in_range(self):
        """Les valeurs de confiance dans la réponse parsée sont dans [0,1]."""
        raw = self._make_valid_json()
        result = parse_vision_response(raw)
        if "overall_confidence" in result and result["overall_confidence"] is not None:
            assert 0.0 <= result["overall_confidence"] <= 1.0


# ── Tests _populate_photo_from_analysis ───────────────────────────────────────

class TestPopulatePhotoFromAnalysis:

    def _make_mock_photo(self) -> MagicMock:
        photo = MagicMock()
        photo.identified_foods = None
        photo.estimated_calories = None
        photo.estimated_protein_g = None
        photo.estimated_carbs_g = None
        photo.estimated_fat_g = None
        photo.confidence_score = None
        photo.ai_analysis = None
        return photo

    def _make_analysis(self) -> dict:
        return {
            "foods": [
                {"name": "Chicken", "quantity_g": 150, "confidence": 0.9},
                {"name": "Rice", "quantity_g": 100, "confidence": 0.8},
            ],
            "estimated_total_calories": 450,
            "estimated_total_protein_g": 35,
            "estimated_total_carbs_g": 40,
            "estimated_total_fat_g": 12,
            "overall_confidence": 0.85,
            "meal_type_guess": "lunch",
            "warnings": [],
            "assumptions": ["Standard cooking"],
            "missing_information": [],
        }

    def test_fields_populated(self):
        photo = self._make_mock_photo()
        analysis = self._make_analysis()
        _populate_photo_from_analysis(photo, analysis)
        assert photo.estimated_calories == 450
        assert photo.estimated_protein_g == 35
        assert photo.estimated_carbs_g == 40
        assert photo.estimated_fat_g == 12
        assert photo.confidence_score == pytest.approx(0.85)

    def test_identified_foods_stored(self):
        photo = self._make_mock_photo()
        analysis = self._make_analysis()
        _populate_photo_from_analysis(photo, analysis)
        assert photo.identified_foods is not None
        assert len(photo.identified_foods) == 2

    def test_ai_analysis_metadata_stored(self):
        photo = self._make_mock_photo()
        analysis = self._make_analysis()
        _populate_photo_from_analysis(photo, analysis)
        meta = photo.ai_analysis
        assert meta is not None
        assert "meal_type_guess" in meta
        assert meta["meal_type_guess"] == "lunch"
        assert "analyzed_at" in meta

    def test_empty_analysis_no_crash(self):
        """Un dict vide ne doit pas lever d'exception."""
        photo = self._make_mock_photo()
        _populate_photo_from_analysis(photo, {})
        # Les champs restent None ou vides
        assert photo.estimated_calories is None

    def test_mock_mode_flag_in_metadata(self):
        """Le flag mock_mode doit apparaître dans ai_analysis."""
        with patch("app.services.vision_service.settings") as mock_settings:
            mock_settings.CLAUDE_VISION_MOCK_MODE = True
            photo = self._make_mock_photo()
            _populate_photo_from_analysis(photo, self._make_analysis())
            assert photo.ai_analysis.get("mock_mode") is True


# ── Tests MEAL_ANALYSIS_PROMPT ─────────────────────────────────────────────────

class TestMealAnalysisPrompt:

    def test_prompt_is_string(self):
        assert isinstance(MEAL_ANALYSIS_PROMPT, str)

    def test_prompt_not_empty(self):
        assert len(MEAL_ANALYSIS_PROMPT) > 100

    def test_prompt_mentions_json(self):
        assert "json" in MEAL_ANALYSIS_PROMPT.lower() or "JSON" in MEAL_ANALYSIS_PROMPT

    def test_prompt_mentions_calories(self):
        assert "calorie" in MEAL_ANALYSIS_PROMPT.lower() or "kcal" in MEAL_ANALYSIS_PROMPT.lower()

"""
Prompts Claude Vision pour l'analyse de photos de repas — SOMA LOT 2.

Design :
  - Prompt en anglais (Claude répond mieux en anglais pour les tâches structurées)
  - Réponse JSON stricte pour parsing fiable
  - Extraction du JSON tolérante (gère les backticks markdown)
"""
import json
import re
from typing import Optional


MEAL_ANALYSIS_PROMPT = """You are a professional nutritionist analyzing a meal photo for a health app.

Analyze this meal photo and respond ONLY with valid JSON in the exact format below.
Do not add any text before or after the JSON. Do not use markdown code fences.

Required JSON format:
{
  "foods": [
    {
      "name": "string (English name)",
      "name_fr": "string (French name, optional)",
      "quantity_g": number_or_null,
      "calories_estimated": number_or_null,
      "protein_g_estimated": number_or_null,
      "carbs_g_estimated": number_or_null,
      "fat_g_estimated": number_or_null,
      "confidence": number_between_0_and_1,
      "food_group": "protein|vegetable|fruit|grain|dairy|fat|processed|other",
      "notes": "string_or_null"
    }
  ],
  "overall_confidence": number_between_0_and_1,
  "meal_type_guess": "breakfast|lunch|dinner|snack|unknown",
  "estimated_total_calories": number_or_null,
  "estimated_total_protein_g": number_or_null,
  "estimated_total_carbs_g": number_or_null,
  "estimated_total_fat_g": number_or_null,
  "warnings": ["string"],
  "assumptions": ["string"],
  "missing_information": ["string"]
}

Rules:
- If you cannot see the food clearly, set confidence < 0.5
- Portions are estimates based on visual cues (plate size, typical servings)
- Include ALL visible food items, including garnishes, sauces, drinks
- If the image is not a meal, set overall_confidence to 0 and foods to []
- Nutritional values must be for the estimated quantity shown (not per 100g)
- Be conservative with estimates — never round up portions
"""


def parse_vision_response(raw_text: str) -> dict:
    """
    Parse la réponse textuelle de Claude Vision en dict Python.

    Tolère :
    - JSON pur
    - JSON enveloppé dans des balises markdown ```json ... ```
    - JSON avec texte avant/après
    - Réponse vide ou malformée → retourne dict d'erreur

    Returns : dict avec la structure attendue, ou dict d'erreur avec 'parse_error': True
    """
    if not raw_text or not raw_text.strip():
        return _error_response("Réponse vide de Claude Vision")

    text = raw_text.strip()

    # Tente 1 : JSON direct
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Tente 2 : Extraction depuis bloc markdown ```json...```
    pattern = r"```(?:json)?\s*([\s\S]*?)```"
    match = re.search(pattern, text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Tente 3 : Extraction du premier objet JSON { ... }
    brace_match = re.search(r"\{[\s\S]*\}", text)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return _error_response(f"Impossible de parser la réponse : {text[:200]}")


def _error_response(message: str) -> dict:
    """Retourne une structure d'erreur standardisée."""
    return {
        "foods": [],
        "overall_confidence": 0.0,
        "meal_type_guess": "unknown",
        "estimated_total_calories": None,
        "estimated_total_protein_g": None,
        "estimated_total_carbs_g": None,
        "estimated_total_fat_g": None,
        "warnings": [message],
        "assumptions": [],
        "missing_information": [],
        "parse_error": True,
    }


def build_mock_analysis() -> dict:
    """
    Réponse simulée pour le mode mock (développement / tests).
    Représente un repas standard : poulet + riz + légumes.
    """
    return {
        "foods": [
            {
                "name": "Grilled chicken breast",
                "name_fr": "Poitrine de poulet grillée",
                "quantity_g": 150.0,
                "calories_estimated": 248.0,
                "protein_g_estimated": 46.5,
                "carbs_g_estimated": 0.0,
                "fat_g_estimated": 5.4,
                "confidence": 0.85,
                "food_group": "protein",
                "notes": "Mock analysis — mode développement",
            },
            {
                "name": "White rice (cooked)",
                "name_fr": "Riz blanc cuit",
                "quantity_g": 180.0,
                "calories_estimated": 234.0,
                "protein_g_estimated": 4.3,
                "carbs_g_estimated": 51.5,
                "fat_g_estimated": 0.4,
                "confidence": 0.80,
                "food_group": "grain",
                "notes": None,
            },
            {
                "name": "Mixed vegetables",
                "name_fr": "Légumes mélangés",
                "quantity_g": 100.0,
                "calories_estimated": 45.0,
                "protein_g_estimated": 2.0,
                "carbs_g_estimated": 9.0,
                "fat_g_estimated": 0.5,
                "confidence": 0.70,
                "food_group": "vegetable",
                "notes": None,
            },
        ],
        "overall_confidence": 0.5,
        "meal_type_guess": "lunch",
        "estimated_total_calories": 527.0,
        "estimated_total_protein_g": 52.8,
        "estimated_total_carbs_g": 60.5,
        "estimated_total_fat_g": 6.3,
        "warnings": [
            "⚠️ Mode mock activé — cette analyse est simulée, pas réelle.",
            "Désactiver CLAUDE_VISION_MOCK_MODE et configurer ANTHROPIC_API_KEY pour une vraie analyse.",
        ],
        "assumptions": ["Repas standard poulet-riz-légumes utilisé comme exemple"],
        "missing_information": [],
    }

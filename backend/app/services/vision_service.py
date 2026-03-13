"""
Service d'analyse photo repas via Claude Vision — SOMA LOT 2.

Modes de fonctionnement :
  CLAUDE_VISION_MOCK_MODE = True (défaut)
    → Réponse simulée, aucune API appelée.
    → Utile en développement et CI.

  CLAUDE_VISION_MOCK_MODE = False
    → Appel réel à l'API Anthropic Claude.
    → Nécessite ANTHROPIC_API_KEY dans .env.

Conçu pour être appelé en BackgroundTask FastAPI :
  background_tasks.add_task(analyze_photo_background, photo_id, photo_path, db)
"""
import base64
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.nutrition import NutritionPhoto
from app.utils.vision_prompt import MEAL_ANALYSIS_PROMPT, parse_vision_response, build_mock_analysis

logger = logging.getLogger(__name__)


async def _call_claude_vision(photo_abs_path: str) -> dict:
    """
    Appel réel à l'API Claude Vision.
    Encode l'image en base64 et envoie le prompt structuré.
    Lève une exception en cas d'erreur API.
    """
    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "Package 'anthropic' non installé. Ajouter 'anthropic' dans requirements.txt."
        )

    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY non configurée. Vérifiez votre fichier .env.")

    path = Path(photo_abs_path)
    if not path.exists():
        raise FileNotFoundError(f"Photo introuvable : {photo_abs_path}")

    # Lecture et encodage base64
    with path.open("rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    # Détection du type MIME depuis l'extension
    ext_to_mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".heic": "image/jpeg"}
    media_type = ext_to_mime.get(path.suffix.lower(), "image/jpeg")

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=settings.CLAUDE_VISION_MODEL,
        max_tokens=2048,
        timeout=settings.CLAUDE_VISION_TIMEOUT_S,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": MEAL_ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    )

    raw_text = message.content[0].text if message.content else ""
    return parse_vision_response(raw_text)


def _populate_photo_from_analysis(photo: NutritionPhoto, analysis: dict) -> None:
    """Remplit les champs de la photo depuis le résultat d'analyse."""
    foods = analysis.get("foods", [])
    photo.identified_foods = foods
    photo.estimated_calories = analysis.get("estimated_total_calories")
    photo.estimated_protein_g = analysis.get("estimated_total_protein_g")
    photo.estimated_carbs_g = analysis.get("estimated_total_carbs_g")
    photo.estimated_fat_g = analysis.get("estimated_total_fat_g")
    photo.confidence_score = analysis.get("overall_confidence")
    photo.ai_analysis = {
        "meal_type_guess": analysis.get("meal_type_guess"),
        "warnings": analysis.get("warnings", []),
        "assumptions": analysis.get("assumptions", []),
        "missing_information": analysis.get("missing_information", []),
        "mock_mode": settings.CLAUDE_VISION_MOCK_MODE,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }


async def analyze_photo_background(
    photo_id: uuid.UUID,
    photo_abs_path: str,
    db: AsyncSession,
) -> None:
    """
    Analyse une photo de repas et met à jour le statut en DB.
    Conçu pour être appelé en tâche de fond (BackgroundTask).

    Workflow :
    1. Marque la photo comme "analyzing"
    2. Appelle Claude Vision (réel ou mock)
    3. Remplit les champs d'analyse sur la photo
    4. Marque "analyzed" (succès) ou "failed" (erreur)
    5. Commit en DB
    """
    # Charge la photo depuis la DB
    result = await db.execute(select(NutritionPhoto).where(NutritionPhoto.id == photo_id))
    photo = result.scalar_one_or_none()
    if not photo:
        logger.warning("Photo %s introuvable pour analyse", photo_id)
        return

    photo.analysis_status = "analyzing"
    await db.flush()

    try:
        if settings.CLAUDE_VISION_MOCK_MODE:
            logger.info("Analyse photo %s — mode mock activé", photo_id)
            analysis = build_mock_analysis()
        else:
            logger.info("Analyse photo %s — appel Claude Vision (%s)", photo_id, settings.CLAUDE_VISION_MODEL)
            analysis = await _call_claude_vision(photo_abs_path)

        _populate_photo_from_analysis(photo, analysis)
        photo.analysis_status = "analyzed"
        logger.info("Analyse photo %s terminée — confiance %.2f", photo_id, photo.confidence_score or 0)

    except Exception as exc:
        logger.error("Erreur analyse photo %s : %s", photo_id, exc)
        photo.analysis_status = "failed"
        photo.ai_analysis = {
            "error": str(exc),
            "error_type": type(exc).__name__,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    await db.commit()

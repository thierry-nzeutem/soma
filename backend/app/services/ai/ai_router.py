"""Routeur IA SOMA - route les requetes selon le plan effectif utilisateur."""
import logging
import os
from typing import Optional

from app.core.features import FeatureCode
from app.core.entitlements import user_has_feature, get_effective_plan
from app.core.plans import PlanCode
from app.models.user import User

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

CLAUDE_STANDARD_MODEL = "claude-3-5-haiku-20241022"
CLAUDE_ADVANCED_MODEL = "claude-3-5-sonnet-20241022"

# Free plan quotas
FREE_PLAN_DAILY_LIMIT = int(os.getenv("FREE_PLAN_DAILY_LIMIT", "10"))
FREE_PLAN_MAX_PROMPT_CHARS = int(os.getenv("FREE_PLAN_MAX_PROMPT_CHARS", "1200"))
FREE_PLAN_TIMEOUT = float(os.getenv("FREE_PLAN_AI_TIMEOUT", "15.0"))

_PERFORMANCE_FEATURES = {
    FeatureCode.BIOMECHANICS_VISION,
    FeatureCode.INJURY_PREDICTION,
    FeatureCode.READINESS_SCORE,
    FeatureCode.ADVANCED_VO2MAX,
    FeatureCode.TRAINING_LOAD,
}


async def _check_free_quota(user: User, db=None) -> bool:
    """Retourne True si l utilisateur free n a pas depasse son quota journalier."""
    if db is None:
        return True
    from sqlalchemy import text
    from datetime import date
    today = date.today().isoformat()
    result = await db.execute(
        text(
            "SELECT COUNT(*) FROM feature_usage_events "
            "WHERE user_id = :uid AND event_type = 'feature_used' "
            "AND DATE(occurred_at) = :today"
        ),
        {"uid": str(user.id), "today": today},
    )
    count = result.scalar() or 0
    return count < FREE_PLAN_DAILY_LIMIT


def _get_ai_tier(user: User, feature: FeatureCode) -> str:
    """Determine le tier IA: local, standard, advanced."""
    effective = get_effective_plan(user)
    if feature == FeatureCode.LOCAL_AI_TIPS:
        return "local"
    if effective == PlanCode.PERFORMANCE and feature in _PERFORMANCE_FEATURES:
        return "advanced"
    if user_has_feature(user, feature):
        return "standard"
    raise PermissionError(f"Feature '{feature.value}' requires plan upgrade")


async def route_ai_request(
    user: User,
    feature: FeatureCode,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    db=None,
) -> str:
    """
    Route vers le bon backend IA selon le plan effectif.
    - free  + LOCAL_AI_TIPS -> Ollama (avec quota journalier)
    - ai    + feature AI    -> Claude Haiku
    - performance + feature -> Claude Sonnet
    """
    tier = _get_ai_tier(user, feature)
    effective = get_effective_plan(user)

    if tier == "local":
        # Check free quota
        if not await _check_free_quota(user, db):
            return "Vous avez atteint votre limite quotidienne de conseils IA. Revenez demain ou passez au plan SOMA AI pour un acces illimite."
        # Truncate long prompts for free plan
        if len(prompt) > FREE_PLAN_MAX_PROMPT_CHARS:
            prompt = prompt[:FREE_PLAN_MAX_PROMPT_CHARS] + "..."
        return await _call_ollama(prompt, system_prompt, max_tokens, timeout=FREE_PLAN_TIMEOUT)

    elif tier == "standard":
        return await _call_claude(prompt, system_prompt, max_tokens, model=CLAUDE_STANDARD_MODEL)
    else:  # advanced
        return await _call_claude(prompt, system_prompt, max_tokens, model=CLAUDE_ADVANCED_MODEL)


async def _call_ollama(prompt: str, system_prompt: Optional[str], max_tokens: int, timeout: float = 30.0) -> str:
    try:
        import httpx
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_prompt or "Tu es un assistant sante bienveillant.",
            "stream": False,
            "options": {"num_predict": min(max_tokens, 256)},
        }
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.warning(f"Ollama unavailable: {e}. Falling back to static tip.")
        return _static_tip()


async def _call_claude(prompt: str, system_prompt: Optional[str], max_tokens: int, model: str) -> str:
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, returning placeholder")
        return f"[IA non configuree - configurez ANTHROPIC_API_KEY] Requete: {prompt[:80]}..."
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        message = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt or "Tu es SOMA, un coach sante IA personalise, bienveillant et expert en sante holistique.",
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        raise RuntimeError(f"Service IA temporairement indisponible: {e}")


def _static_tip() -> str:
    import random
    tips = [
        "Buvez au moins 2L d eau par jour pour maintenir votre energie.",
        "Une marche de 30 minutes par jour reduit les risques cardiovasculaires.",
        "Couchez-vous et levez-vous a la meme heure chaque jour.",
        "Incluez des proteines a chaque repas pour maintenir la masse musculaire.",
    ]
    return random.choice(tips)

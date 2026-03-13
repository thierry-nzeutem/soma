"""
Claude Client — SOMA LOT 9 (Coach IA).

Wrapper autour de l'API Anthropic pour le coach conversationnel.
Pattern identique à vision_service.py :
  CLAUDE_COACH_MOCK_MODE = True (défaut) → réponse simulée sans API
  CLAUDE_COACH_MOCK_MODE = False          → appel réel à l'API Anthropic

Fonctions :
  generate_coach_reply()  → str  (réponse brute du LLM)
  build_mock_reply()      → str  (réponse simulée déterministe pour tests)
"""
import json
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── System prompt ─────────────────────────────────────────────────────────────

COACH_SYSTEM_PROMPT = """Tu es SOMA, un coach santé personnalisé intelligent et bienveillant.
Tu as accès aux données physiologiques réelles de l'utilisateur (sommeil, nutrition, entraînement, récupération, scores longévité).

Règles impératives :
- Explique clairement et simplement, sans jargon médical inutile.
- Cite toujours les signaux que tu utilises pour ta réponse (ex: "ton score de récupération de 72/100 indique...").
- Reste concis : 3-5 phrases de synthèse, puis des recommandations concrètes en bullet points.
- Ne jamais inventer de données. Si l'information est absente ou incertaine, dis-le explicitement.
- Ne jamais donner de conseils médicaux qui remplacent un médecin. Invite à consulter si nécessaire.
- Utilise le vouvoiement ou tutoiement selon la culture francophone (tutoiement par défaut).
- Donne des recommandations actionnables, prioritaires, et adaptées au contexte du jour.

Structure ta réponse ainsi :
1. Synthèse (1-2 phrases sur l'état du jour)
2. Points clés observés (2-4 bullet points)
3. Recommandations concrètes (2-4 bullet points)
4. Si des alertes ou risques : ajoute une section ⚠ Vigilance"""


# ── Appel réel à l'API ────────────────────────────────────────────────────────

async def generate_coach_reply(
    question: str,
    context_text: str,
    conversation_history: Optional[list[dict]] = None,
) -> str:
    """
    Génère une réponse du coach SOMA via Claude API.

    Args:
        question: Question de l'utilisateur.
        context_text: Contexte physiologique formaté (issu de CoachContext.to_prompt_text()).
        conversation_history: Historique de conversation [{role, content}, ...] (optionnel).

    Returns:
        Réponse textuelle du coach.
    """
    if settings.CLAUDE_COACH_MOCK_MODE:
        logger.info("Coach réponse — mode mock activé")
        return _build_mock_reply(question, context_text)

    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError(
            "ANTHROPIC_API_KEY non configurée. Vérifiez votre fichier .env."
        )

    try:
        import anthropic
    except ImportError:
        raise RuntimeError(
            "Package 'anthropic' non installé. Exécutez : pip install anthropic"
        )

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Construire les messages
    messages: list[dict] = []

    # Historique précédent (si fourni, max 10 échanges)
    if conversation_history:
        messages.extend(conversation_history[-10:])

    # Message courant : contexte + question
    user_message = f"=== CONTEXTE PHYSIOLOGIQUE DU JOUR ===\n{context_text}\n\n=== QUESTION ===\n{question}"
    messages.append({"role": "user", "content": user_message})

    logger.info(
        "Appel Claude Coach (%s) — question: %s...",
        settings.CLAUDE_COACH_MODEL,
        question[:60],
    )

    response = await client.messages.create(
        model=settings.CLAUDE_COACH_MODEL,
        max_tokens=settings.CLAUDE_COACH_MAX_TOKENS,
        temperature=settings.CLAUDE_COACH_TEMPERATURE,
        timeout=settings.CLAUDE_COACH_TIMEOUT_S,
        system=COACH_SYSTEM_PROMPT,
        messages=messages,
    )

    reply = response.content[0].text if response.content else ""
    logger.info("Coach réponse générée (%d caractères)", len(reply))
    return reply


# ── Mode mock ─────────────────────────────────────────────────────────────────

def _build_mock_reply(question: str, context_text: str) -> str:
    """
    Réponse simulée déterministe pour le développement et les tests.
    Analyse le contexte et la question pour produire une réponse pertinente.
    """
    q_lower = question.lower()

    # Détection de mots-clés dans la question
    if any(w in q_lower for w in ["fatigué", "fatigue", "tired", "épuisé"]):
        return (
            "**Synthèse** : Ton niveau de fatigue est élevé aujourd'hui d'après tes données.\n\n"
            "**Points clés observés** :\n"
            "• Charge d'entraînement élevée sur les 7 derniers jours\n"
            "• Score de récupération sous le seuil optimal\n"
            "• Qualité de sommeil à améliorer\n\n"
            "**Recommandations** :\n"
            "• Privilégie une séance légère ou du repos actif aujourd'hui\n"
            "• Vise 7h30-8h de sommeil cette nuit\n"
            "• Assure-toi d'atteindre ton objectif d'hydratation (2000+ ml)\n"
            "• Augmente tes apports en protéines pour accélérer la récupération"
        )
    elif any(w in q_lower for w in ["manger", "nutrition", "repas", "eat", "food", "soir"]):
        return (
            "**Synthèse** : D'après tes données nutritionnelles du jour, voici mes recommandations.\n\n"
            "**Points clés observés** :\n"
            "• Apports caloriques et distribution des macronutriments analysés\n"
            "• Statut protéique et hydratation pris en compte\n\n"
            "**Recommandations** :\n"
            "• Pour ce soir : privilégie une source de protéines maigres (150-200g)\n"
            "• Ajoute des légumes riches en fibres et des glucides complexes\n"
            "• Évite les sucres rapides après 19h pour optimiser ton sommeil\n"
            "• Bois encore au moins 500ml d'eau avant de dormir"
        )
    elif any(w in q_lower for w in ["entraîn", "sport", "workout", "séance", "train"]):
        return (
            "**Synthèse** : Voici une recommandation d'entraînement basée sur ton état du jour.\n\n"
            "**Points clés observés** :\n"
            "• Intensité recommandée basée sur ton score de récupération\n"
            "• Charge d'entraînement hebdomadaire analysée\n\n"
            "**Recommandations** :\n"
            "• Intensité adaptée à ton niveau de récupération actuel\n"
            "• Inclus 10 min d'échauffement progressif\n"
            "• Concentre-toi sur les groupes musculaires non sollicités récemment\n"
            "• Termine par 5-10 min d'étirements pour accélérer la récupération"
        )
    elif any(w in q_lower for w in ["analyse", "bilan", "journée", "day", "résumé", "summary"]):
        return (
            "**Synthèse** : Voici l'analyse complète de ta journée basée sur tes données SOMA.\n\n"
            "**Points clés observés** :\n"
            "• Récupération, nutrition, hydratation et entraînement analysés\n"
            "• Métriques physiologiques comparées à tes objectifs\n"
            "• Tendances sur les 7 derniers jours prises en compte\n\n"
            "**Recommandations** :\n"
            "• Maintiens ta régularité dans les prochains jours\n"
            "• Priorise le sommeil pour optimiser ta récupération\n"
            "• Ajuste tes apports si tu n'atteins pas tes cibles macro\n"
            "• Planifie ta prochaine séance selon l'intensité recommandée"
        )
    else:
        return (
            "**Synthèse** : J'ai analysé tes données physiologiques pour répondre à ta question.\n\n"
            "**Points clés observés** :\n"
            "• Données de récupération, nutrition et entraînement disponibles\n"
            "• Contexte métabolique du jour pris en compte\n\n"
            "**Recommandations** :\n"
            "• Continue à enregistrer tes données quotidiennement pour un suivi précis\n"
            "• Consulte ton plan santé du jour pour les recommandations détaillées\n"
            "• N'hésite pas à me poser des questions spécifiques sur ta nutrition, "
            "ton entraînement ou ta récupération"
        )

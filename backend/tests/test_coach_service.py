"""
Tests unitaires — coach_service.py + claude_client.py (LOT 9).

Couvre :
  - _parse_coach_reply() : extraction summary / recommendations / warnings
  - _build_mock_reply() : réponses mock par mot-clé
  - generate_coach_reply() : mode mock (sans API réelle)
  - create_thread() : création thread DB
  - get_threads() : liste threads utilisateur
  - get_messages() : messages + vérification propriété
  - ask_coach() : flow complet en mode mock

Stratégie :
  - Fonctions pures testées directement (pas de DB)
  - Fonctions DB testées via db_session (SQLite in-memory)
  - Claude API moquée via CLAUDE_COACH_MOCK_MODE=True (défaut)
"""
import pytest
import uuid
from datetime import date
from unittest.mock import patch, AsyncMock

from app.services.coach_service import (
    _parse_coach_reply,
    ask_coach,
    create_thread,
    get_messages,
    get_threads,
)
from app.services.claude_client import _build_mock_reply, generate_coach_reply


# ── _parse_coach_reply ────────────────────────────────────────────────────────

class TestParseCoachReply:

    _sample_reply = (
        "**Synthèse** : Ton niveau de fatigue est élevé.\n\n"
        "**Points clés observés** :\n"
        "• Charge d'entraînement élevée\n"
        "• Récupération insuffisante\n\n"
        "**Recommandations** :\n"
        "- Réduis l'intensité aujourd'hui\n"
        "- Dors 8h cette nuit\n"
        "- Bois 2L d'eau\n\n"
        "⚠ Vigilance : FC repos élevée, surveille ton état\n"
    )

    def test_returns_tuple_of_three(self):
        result = _parse_coach_reply(self._sample_reply)
        assert len(result) == 3

    def test_summary_extracted(self):
        summary, _, _ = _parse_coach_reply(self._sample_reply)
        assert "fatigue" in summary.lower()

    def test_summary_is_not_full_text(self):
        summary, _, _ = _parse_coach_reply(self._sample_reply)
        # La synthèse doit être une phrase, pas tout le texte
        assert len(summary) < len(self._sample_reply)

    def test_recommendations_extracted(self):
        _, recs, _ = _parse_coach_reply(self._sample_reply)
        assert isinstance(recs, list)
        assert len(recs) >= 2

    def test_recommendations_not_empty_strings(self):
        _, recs, _ = _parse_coach_reply(self._sample_reply)
        for rec in recs:
            assert rec.strip() != ""

    def test_warnings_extracted(self):
        _, _, warnings = _parse_coach_reply(self._sample_reply)
        assert isinstance(warnings, list)
        assert len(warnings) >= 1
        assert any("FC" in w or "surveill" in w for w in warnings)

    def test_no_warnings_when_none(self):
        reply = "**Synthèse** : Tout va bien.\n\n**Recommandations** :\n- Continue !\n"
        _, _, warnings = _parse_coach_reply(reply)
        assert warnings == []

    def test_fallback_summary_is_full_text_when_no_marker(self):
        plain = "Voici ma réponse sans structure."
        summary, recs, warnings = _parse_coach_reply(plain)
        assert summary == plain
        assert recs == []
        assert warnings == []

    def test_recommendations_cleaned_of_bullets(self):
        reply = "**Recommandations** :\n• Item A\n- Item B\n* Item C\n\nFin\n"
        _, recs, _ = _parse_coach_reply(reply)
        for rec in recs:
            assert not rec.startswith("•")
            assert not rec.startswith("-")
            assert not rec.startswith("*")


# ── _build_mock_reply ─────────────────────────────────────────────────────────

class TestBuildMockReply:

    def test_returns_string(self):
        result = _build_mock_reply("Bonjour", "context")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fatigue_keyword_triggers_fatigue_response(self):
        result = _build_mock_reply("Je suis fatigué aujourd'hui", "context")
        assert "fatigue" in result.lower() or "récupération" in result.lower()

    def test_nutrition_keyword_triggers_nutrition_response(self):
        result = _build_mock_reply("Que dois-je manger ce soir ?", "context")
        assert "nutrition" in result.lower() or "protéines" in result.lower() or "repas" in result.lower()

    def test_workout_keyword_triggers_workout_response(self):
        result = _build_mock_reply("Quelle séance faire aujourd'hui ?", "context")
        assert "entraînement" in result.lower() or "séance" in result.lower() or "intensité" in result.lower()

    def test_analyse_keyword_triggers_bilan_response(self):
        result = _build_mock_reply("Fais une analyse de ma journée", "context")
        assert "journée" in result.lower() or "analyse" in result.lower() or "bilan" in result.lower()

    def test_unknown_question_gives_generic_response(self):
        result = _build_mock_reply("Qu'est-ce que le zinc ?", "context")
        assert "**Synthèse**" in result

    def test_all_responses_have_synthese(self):
        questions = [
            "Je suis fatigué",
            "Que manger ?",
            "Faire du sport ?",
            "Analyse ma journée",
            "Question inconnue xyz",
        ]
        for q in questions:
            result = _build_mock_reply(q, "context")
            assert "**Synthèse**" in result, f"Synthèse absente pour: {q}"

    def test_all_responses_have_recommandations(self):
        questions = ["fatigue", "nutrition", "entraîn", "bilan", "inconnu"]
        for q in questions:
            result = _build_mock_reply(q, "")
            assert "Recommandations" in result, f"Recommandations absentes pour: {q}"


# ── generate_coach_reply (mode mock) ──────────────────────────────────────────

class TestGenerateCoachReplyMock:

    @pytest.mark.asyncio
    async def test_mock_mode_returns_string(self):
        result = await generate_coach_reply(
            question="Comment améliorer ma récupération ?",
            context_text="Contexte test",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_mock_mode_does_not_call_anthropic(self):
        """En mode mock, l'API Anthropic ne doit jamais être appelée."""
        with patch("anthropic.AsyncAnthropic") as mock_client:
            result = await generate_coach_reply(
                question="test", context_text="ctx",
            )
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_mock_mode_with_conversation_history(self):
        history = [
            {"role": "user", "content": "Ma question précédente"},
            {"role": "assistant", "content": "Ma réponse précédente"},
        ]
        result = await generate_coach_reply(
            question="Nouvelle question",
            context_text="ctx",
            conversation_history=history,
        )
        assert isinstance(result, str)


# ── create_thread ─────────────────────────────────────────────────────────────

class TestCreateThread:

    @pytest.mark.asyncio
    async def test_creates_thread_with_title(self, db_session):
        user_id = uuid.uuid4()
        thread = await create_thread(db_session, user_id, title="Mon thread test")
        await db_session.flush()
        assert thread.id is not None
        assert thread.title == "Mon thread test"
        assert thread.user_id == user_id

    @pytest.mark.asyncio
    async def test_creates_thread_without_title(self, db_session):
        user_id = uuid.uuid4()
        thread = await create_thread(db_session, user_id)
        await db_session.flush()
        assert thread.title == "Nouvelle conversation"

    @pytest.mark.asyncio
    async def test_thread_has_id(self, db_session):
        user_id = uuid.uuid4()
        thread = await create_thread(db_session, user_id, title="Test")
        assert isinstance(thread.id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_two_threads_different_ids(self, db_session):
        user_id = uuid.uuid4()
        t1 = await create_thread(db_session, user_id, title="Thread 1")
        t2 = await create_thread(db_session, user_id, title="Thread 2")
        assert t1.id != t2.id


# ── get_threads ───────────────────────────────────────────────────────────────

class TestGetThreads:

    @pytest.mark.asyncio
    async def test_empty_for_new_user(self, db_session):
        user_id = uuid.uuid4()
        threads = await get_threads(db_session, user_id)
        assert threads == []

    @pytest.mark.asyncio
    async def test_returns_user_threads_only(self, db_session):
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        await create_thread(db_session, user_a, title="Thread A")
        await create_thread(db_session, user_b, title="Thread B")
        await db_session.flush()

        threads_a = await get_threads(db_session, user_a)
        threads_b = await get_threads(db_session, user_b)
        assert len(threads_a) == 1
        assert len(threads_b) == 1
        assert threads_a[0].title == "Thread A"

    @pytest.mark.asyncio
    async def test_limit_respected(self, db_session):
        user_id = uuid.uuid4()
        for i in range(5):
            await create_thread(db_session, user_id, title=f"Thread {i}")
        await db_session.flush()

        threads = await get_threads(db_session, user_id, limit=3)
        assert len(threads) <= 3


# ── get_messages ──────────────────────────────────────────────────────────────

class TestGetMessages:

    @pytest.mark.asyncio
    async def test_empty_thread_returns_no_messages(self, db_session):
        user_id = uuid.uuid4()
        thread = await create_thread(db_session, user_id, title="Test")
        await db_session.flush()
        messages = await get_messages(db_session, thread.id, user_id)
        assert messages == []

    @pytest.mark.asyncio
    async def test_wrong_user_raises_permission_error(self, db_session):
        owner_id = uuid.uuid4()
        other_id = uuid.uuid4()
        thread = await create_thread(db_session, owner_id, title="Test")
        await db_session.flush()

        with pytest.raises(PermissionError):
            await get_messages(db_session, thread.id, other_id)

    @pytest.mark.asyncio
    async def test_unknown_thread_raises_permission_error(self, db_session):
        user_id = uuid.uuid4()
        fake_thread_id = uuid.uuid4()

        with pytest.raises(PermissionError):
            await get_messages(db_session, fake_thread_id, user_id)


# ── ask_coach (intégration, mode mock) ────────────────────────────────────────

class TestAskCoach:

    @pytest.mark.asyncio
    async def test_ask_coach_returns_coach_answer(self, db_session):
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Pourquoi suis-je fatigué ?",
        )
        assert answer is not None
        assert isinstance(answer.full_response, str)
        assert len(answer.full_response) > 0

    @pytest.mark.asyncio
    async def test_ask_coach_creates_thread_when_none(self, db_session):
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Analyse ma journée",
        )
        assert answer.thread_id is not None
        assert isinstance(answer.thread_id, uuid.UUID)

    @pytest.mark.asyncio
    async def test_ask_coach_message_id_set(self, db_session):
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Comment optimiser ma récupération ?",
        )
        assert answer.message_id is not None

    @pytest.mark.asyncio
    async def test_ask_coach_confidence_between_0_and_1(self, db_session):
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Que manger ce soir ?",
        )
        assert 0.0 <= answer.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_ask_coach_with_existing_thread(self, db_session):
        user_id = uuid.uuid4()
        # Crée d'abord un thread
        thread = await create_thread(db_session, user_id, title="Conversation test")
        await db_session.flush()

        # Pose une question dans ce thread
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Question de suivi",
            thread_id=thread.id,
        )
        assert answer.thread_id == thread.id

    @pytest.mark.asyncio
    async def test_ask_coach_wrong_thread_raises_permission_error(self, db_session):
        user_id = uuid.uuid4()
        other_user_id = uuid.uuid4()
        # Thread appartenant à un autre utilisateur
        thread = await create_thread(db_session, other_user_id, title="Autre user")
        await db_session.flush()

        with pytest.raises(PermissionError):
            await ask_coach(
                db=db_session,
                user_id=user_id,
                question="Question non autorisée",
                thread_id=thread.id,
            )

    @pytest.mark.asyncio
    async def test_ask_coach_model_used_mock(self, db_session):
        """En mode mock, model_used doit être 'mock'."""
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Test mock mode",
        )
        assert answer.model_used == "mock"

    @pytest.mark.asyncio
    async def test_ask_coach_summary_not_empty(self, db_session):
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Analyse mes données",
        )
        assert answer.summary
        assert len(answer.summary) > 0

    @pytest.mark.asyncio
    async def test_ask_coach_recommendations_list(self, db_session):
        user_id = uuid.uuid4()
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Je suis fatigué, aide moi",
        )
        assert isinstance(answer.recommendations, list)

    @pytest.mark.asyncio
    async def test_ask_coach_with_target_date(self, db_session):
        user_id = uuid.uuid4()
        target = date(2026, 3, 7)
        answer = await ask_coach(
            db=db_session,
            user_id=user_id,
            question="Bilan du jour",
            target_date=target,
        )
        assert answer is not None

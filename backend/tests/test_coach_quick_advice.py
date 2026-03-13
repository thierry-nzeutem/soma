"""
SOMA LOT 18 — Tests unitaires Coach Quick Advice.

Couvre :
  - QuickAdviceRequest : validation Pydantic (min_length, max_length)
  - QuickAdviceResponse : structure et champs
  - _parse_quick_reply() : parsing des sections Réponse/À faire/Alerte
  - context_builder : limite 6000 chars + twin_key_signals field
  - MAX_CONTEXT_CHARS = 6000 dans context_builder

~12 tests purs, aucune dépendance DB.
"""
import pytest
from pydantic import ValidationError

from app.schemas.coach import QuickAdviceRequest, QuickAdviceResponse
from app.api.v1.endpoints.coach import _parse_quick_reply
from app.services.context_builder import _MAX_CONTEXT_CHARS, CoachContext


# ── Tests QuickAdviceRequest ────────────────────────────────────────────────

class TestQuickAdviceRequest:
    """Validation de la requête conseil rapide."""

    def test_valid_question(self):
        req = QuickAdviceRequest(question="Dois-je m'entraîner aujourd'hui ?")
        assert len(req.question) > 0

    def test_min_length_3(self):
        with pytest.raises(ValidationError):
            QuickAdviceRequest(question="ok")

    def test_3_chars_valid(self):
        req = QuickAdviceRequest(question="OK?")
        assert req.question == "OK?"

    def test_max_length_500(self):
        with pytest.raises(ValidationError):
            QuickAdviceRequest(question="x" * 501)

    def test_500_chars_valid(self):
        req = QuickAdviceRequest(question="x" * 500)
        assert len(req.question) == 500


# ── Tests QuickAdviceResponse ────────────────────────────────────────────────

class TestQuickAdviceResponse:
    """Structure de la réponse conseil rapide."""

    def _make_response(self, **overrides) -> dict:
        base = {
            "answer": "Tu es en bonne forme pour t'entraîner.",
            "recommendations": ["Fais 45 min de cardio", "Hydrate-toi bien"],
            "alert": None,
            "confidence": 0.72,
            "model_used": "mock",
            "context_summary": "readiness: 82%, fatigue: 30%, twin: good",
        }
        base.update(overrides)
        return base

    def test_valid_response(self):
        resp = QuickAdviceResponse(**self._make_response())
        assert resp.confidence == 0.72
        assert resp.model_used == "mock"

    def test_alert_is_none_by_default(self):
        resp = QuickAdviceResponse(**self._make_response(alert=None))
        assert resp.alert is None

    def test_alert_can_be_string(self):
        resp = QuickAdviceResponse(**self._make_response(alert="ACWR critique > 1.8"))
        assert "ACWR" in resp.alert

    def test_recommendations_list(self):
        resp = QuickAdviceResponse(**self._make_response())
        assert isinstance(resp.recommendations, list)
        assert len(resp.recommendations) == 2

    def test_context_summary_format(self):
        resp = QuickAdviceResponse(**self._make_response())
        assert "readiness" in resp.context_summary

    def test_confidence_range_0_to_1(self):
        with pytest.raises(ValidationError):
            QuickAdviceResponse(**self._make_response(confidence=1.5))
        with pytest.raises(ValidationError):
            QuickAdviceResponse(**self._make_response(confidence=-0.1))


# ── Tests _parse_quick_reply() ──────────────────────────────────────────────

class TestParseQuickReply:
    """Parsing de la réponse quick-advice en sections structurées."""

    def _make_reply(
        self,
        answer="Tu es bien récupéré pour t'entraîner.",
        actions=("Fais du cardio 45min", "Hydrate-toi"),
        alert=None,
    ) -> str:
        lines = [f"**Réponse**: {answer}\n"]
        lines.append("**À faire**: ")
        for a in actions:
            lines.append(f"- {a}")
        if alert:
            lines.append(f"\n**Alerte**: {alert}")
        return "\n".join(lines)

    def test_answer_extracted(self):
        raw = self._make_reply()
        answer, recs, alert = _parse_quick_reply(raw)
        assert "récupéré" in answer

    def test_recommendations_extracted(self):
        raw = self._make_reply()
        _, recs, _ = _parse_quick_reply(raw)
        assert len(recs) >= 1
        assert any("cardio" in r.lower() for r in recs)

    def test_recommendations_max_2(self):
        raw = self._make_reply(actions=("Action 1", "Action 2", "Action 3"))
        _, recs, _ = _parse_quick_reply(raw)
        assert len(recs) <= 2

    def test_no_alert_returns_none(self):
        raw = self._make_reply()
        _, _, alert = _parse_quick_reply(raw)
        assert alert is None

    def test_alert_extracted(self):
        raw = self._make_reply(alert="ACWR critique > 1.8, risque blessure")
        _, _, alert = _parse_quick_reply(raw)
        assert alert is not None
        assert "ACWR" in alert

    def test_fallback_on_empty_sections(self):
        """Si les sections sont absentes, l'answer est le raw brut tronqué."""
        raw = "Voici ma réponse sans structure."
        answer, recs, alert = _parse_quick_reply(raw)
        assert len(answer) > 0


# ── Tests context_builder LOT 18 ────────────────────────────────────────────

class TestContextBuilderLot18:
    """Vérification des modifications LOT 18 du context_builder."""

    def test_max_context_chars_is_6000(self):
        """La limite doit être 6000 (était 5500)."""
        assert _MAX_CONTEXT_CHARS == 6_000

    def test_coachcontext_has_twin_key_signals_field(self):
        """CoachContext doit avoir le champ twin_key_signals."""
        ctx = CoachContext(today_date="2026-03-08")
        assert hasattr(ctx, "twin_key_signals")
        assert ctx.twin_key_signals is None  # valeur par défaut

    def test_twin_key_signals_rendered_in_prompt(self):
        """Si twin_key_signals est défini, il apparaît dans to_prompt_text()."""
        ctx = CoachContext(today_date="2026-03-08")
        ctx.twin_key_signals = "• Training Readiness: 72/100 (good)\n• Fatigue: 45/100 (moderate)"
        text = ctx.to_prompt_text()
        assert "SIGNAUX CLÉS JUMEAU" in text
        assert "Training Readiness" in text

    def test_twin_key_signals_not_rendered_when_none(self):
        """Si twin_key_signals est None, la section n'apparaît pas."""
        ctx = CoachContext(today_date="2026-03-08")
        ctx.twin_key_signals = None
        text = ctx.to_prompt_text()
        assert "SIGNAUX CLÉS JUMEAU" not in text

    def test_prompt_text_truncated_at_6000(self):
        """to_prompt_text() ne doit pas dépasser 6000 caractères."""
        ctx = CoachContext(today_date="2026-03-08")
        # Remplir avec beaucoup de contenu
        ctx.learning_summary = "x" * 2000
        ctx.biomarker_summary = "y" * 2000
        ctx.injury_risk_summary = "z" * 2000
        text = ctx.to_prompt_text()
        assert len(text) <= 6_000 + 50  # + marge pour "[contexte tronqué]"

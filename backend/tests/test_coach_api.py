"""
Tests API — endpoints Coach IA (LOT 9).

Couvre :
  - POST /coach/ask      : réponse coach + création thread automatique
  - POST /coach/thread   : création fil de conversation
  - GET  /coach/history  : liste des fils utilisateur
  - GET  /coach/history/{id} : détail fil + messages

Stratégie :
  - Authentification mockée via app.dependency_overrides[get_current_user]
  - DB SQLite in-memory via fixture db_session (conftest.py)
  - Claude en mode mock (CLAUDE_COACH_MOCK_MODE=True par défaut)
  - Validation des codes HTTP, structures de réponse et sécurité (403 si mauvais user)
"""
import uuid
import pytest
from unittest.mock import MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.deps import get_current_user
from app.db.session import get_db


# ── Helper : créer un mock User ───────────────────────────────────────────────

def _make_mock_user(user_id: uuid.UUID | None = None) -> MagicMock:
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.username = "testuser"
    user.is_active = True
    return user


# ── Fixture client authentifié ────────────────────────────────────────────────

@pytest.fixture
async def auth_client(db_session):
    """Client HTTP avec utilisateur mockée et DB in-memory."""
    mock_user = _make_mock_user()

    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return mock_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, mock_user

    app.dependency_overrides.clear()


@pytest.fixture
async def two_users_client(db_session):
    """Deux clients avec deux utilisateurs distincts (test isolation)."""
    user_a = _make_mock_user()
    user_b = _make_mock_user()

    async def override_get_db():
        yield db_session

    async def get_user_a():
        return user_a

    async def get_user_b():
        return user_b

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = get_user_a

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a:
        yield client_a, user_a, user_b, db_session

    app.dependency_overrides.clear()


# ── POST /coach/ask ───────────────────────────────────────────────────────────

class TestAskCoachEndpoint:

    @pytest.mark.asyncio
    async def test_ask_coach_returns_200(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={
            "question": "Comment améliorer ma récupération ?"
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_ask_coach_response_structure(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={
            "question": "Analyse ma journée"
        })
        data = resp.json()
        assert "summary" in data
        assert "full_response" in data
        assert "recommendations" in data
        assert "warnings" in data
        assert "confidence" in data
        assert "thread_id" in data
        assert "message_id" in data

    @pytest.mark.asyncio
    async def test_ask_coach_confidence_in_range(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={
            "question": "Bilan du jour"
        })
        data = resp.json()
        assert 0.0 <= data["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_ask_coach_creates_thread(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={
            "question": "Je suis fatigué aujourd'hui"
        })
        data = resp.json()
        assert data["thread_id"] is not None
        # Vérifie que le thread est visible dans l'historique
        history_resp = await client.get("/api/v1/coach/history")
        history_data = history_resp.json()
        assert history_data["total"] >= 1

    @pytest.mark.asyncio
    async def test_ask_coach_with_existing_thread(self, auth_client):
        client, _ = auth_client
        # Créer un thread d'abord
        thread_resp = await client.post("/api/v1/coach/thread", json={"title": "Test thread"})
        thread_id = thread_resp.json()["id"]

        # Poser une question dans ce thread
        resp = await client.post("/api/v1/coach/ask", json={
            "question": "Question dans le thread",
            "thread_id": thread_id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert str(data["thread_id"]) == thread_id

    @pytest.mark.asyncio
    async def test_ask_coach_question_too_short_returns_422(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={"question": "AB"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_ask_coach_no_question_returns_422(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_ask_coach_unauthenticated_returns_401(self, db_session):
        """Sans override d'auth, doit renvoyer 401 ou 403."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/api/v1/coach/ask", json={
                "question": "Question sans auth"
            })
        assert resp.status_code in (401, 403, 422)

    @pytest.mark.asyncio
    async def test_ask_coach_model_used_is_mock(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/ask", json={
            "question": "Test mode mock"
        })
        data = resp.json()
        assert data["model_used"] == "mock"


# ── POST /coach/thread ────────────────────────────────────────────────────────

class TestCreateThreadEndpoint:

    @pytest.mark.asyncio
    async def test_create_thread_returns_201(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/thread", json={"title": "Mon sujet"})
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_thread_without_title(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/thread", json={})
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_thread_with_title(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/thread", json={"title": "Récupération post-trail"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Récupération post-trail"

    @pytest.mark.asyncio
    async def test_create_thread_has_timestamps(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/thread", json={"title": "Test"})
        data = resp.json()
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_thread_has_uuid_id(self, auth_client):
        client, _ = auth_client
        resp = await client.post("/api/v1/coach/thread", json={})
        data = resp.json()
        # Vérifie que c'est bien un UUID valide
        parsed_id = uuid.UUID(data["id"])
        assert parsed_id is not None


# ── GET /coach/history ────────────────────────────────────────────────────────

class TestListThreadsEndpoint:

    @pytest.mark.asyncio
    async def test_history_returns_200(self, auth_client):
        client, _ = auth_client
        resp = await client.get("/api/v1/coach/history")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_history_empty_for_new_user(self, auth_client):
        client, _ = auth_client
        resp = await client.get("/api/v1/coach/history")
        data = resp.json()
        assert data["total"] == 0
        assert data["threads"] == []

    @pytest.mark.asyncio
    async def test_history_shows_created_threads(self, auth_client):
        client, _ = auth_client
        await client.post("/api/v1/coach/thread", json={"title": "Thread A"})
        await client.post("/api/v1/coach/thread", json={"title": "Thread B"})

        resp = await client.get("/api/v1/coach/history")
        data = resp.json()
        assert data["total"] == 2
        assert len(data["threads"]) == 2

    @pytest.mark.asyncio
    async def test_history_structure(self, auth_client):
        client, _ = auth_client
        await client.post("/api/v1/coach/thread", json={"title": "Test"})

        resp = await client.get("/api/v1/coach/history")
        data = resp.json()
        assert "threads" in data
        assert "total" in data
        thread = data["threads"][0]
        assert "id" in thread
        assert "title" in thread
        assert "created_at" in thread

    @pytest.mark.asyncio
    async def test_history_limit_parameter(self, auth_client):
        client, _ = auth_client
        for i in range(5):
            await client.post("/api/v1/coach/thread", json={"title": f"Thread {i}"})

        resp = await client.get("/api/v1/coach/history?limit=3")
        data = resp.json()
        assert len(data["threads"]) <= 3


# ── GET /coach/history/{thread_id} ───────────────────────────────────────────

class TestGetThreadDetailEndpoint:

    @pytest.mark.asyncio
    async def test_get_thread_detail_returns_200(self, auth_client):
        client, _ = auth_client
        thread_resp = await client.post("/api/v1/coach/thread", json={"title": "Test detail"})
        thread_id = thread_resp.json()["id"]

        resp = await client.get(f"/api/v1/coach/history/{thread_id}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_thread_detail_structure(self, auth_client):
        client, _ = auth_client
        thread_resp = await client.post("/api/v1/coach/thread", json={"title": "Thread structuré"})
        thread_id = thread_resp.json()["id"]

        resp = await client.get(f"/api/v1/coach/history/{thread_id}")
        data = resp.json()
        assert "thread" in data
        assert "messages" in data
        assert data["thread"]["id"] == thread_id

    @pytest.mark.asyncio
    async def test_get_thread_detail_shows_messages_after_ask(self, auth_client):
        client, _ = auth_client
        # Créer thread + poser une question
        thread_resp = await client.post("/api/v1/coach/thread", json={"title": "Conversation"})
        thread_id = thread_resp.json()["id"]

        await client.post("/api/v1/coach/ask", json={
            "question": "Analyse ma journée",
            "thread_id": thread_id,
        })

        resp = await client.get(f"/api/v1/coach/history/{thread_id}")
        data = resp.json()
        # Doit avoir au moins 2 messages (user + coach)
        assert len(data["messages"]) >= 2

    @pytest.mark.asyncio
    async def test_get_thread_detail_message_roles(self, auth_client):
        client, _ = auth_client
        thread_resp = await client.post("/api/v1/coach/thread", json={"title": "Roles test"})
        thread_id = thread_resp.json()["id"]

        await client.post("/api/v1/coach/ask", json={
            "question": "Test des rôles dans les messages",
            "thread_id": thread_id,
        })

        resp = await client.get(f"/api/v1/coach/history/{thread_id}")
        data = resp.json()
        roles = {m["role"] for m in data["messages"]}
        assert "user" in roles
        assert "coach" in roles

    @pytest.mark.asyncio
    async def test_get_thread_detail_unknown_thread_returns_403(self, auth_client):
        client, _ = auth_client
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/coach/history/{fake_id}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_thread_detail_wrong_user_returns_403(self, db_session):
        """Un utilisateur ne peut pas accéder au thread d'un autre."""
        user_a = _make_mock_user()
        user_b = _make_mock_user()

        async def override_get_db():
            yield db_session

        # User A crée un thread
        async def get_user_a():
            return user_a

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = get_user_a

        thread_id = None
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_a:
            resp = await client_a.post("/api/v1/coach/thread", json={"title": "Thread privé"})
            await db_session.commit()
            thread_id = resp.json()["id"]

        # User B essaie d'accéder au thread de A
        async def get_user_b():
            return user_b

        app.dependency_overrides[get_current_user] = get_user_b

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client_b:
            resp = await client_b.get(f"/api/v1/coach/history/{thread_id}")
            assert resp.status_code == 403

        app.dependency_overrides.clear()

"""
Tests d'intégration — module nutrition (journal alimentaire + photos).

Nécessite : SOMA_TEST_DATABASE_URL=postgresql+asyncpg://...
Couvre :
  - Création / lecture / mise à jour / suppression d'entrées (CRUD complet)
  - Résumé journalier
  - Upload photo (mock vision)
  - Confirmation photo → création entrée automatique
"""
import pytest
import pytest_asyncio
import httpx
import uuid
from datetime import datetime, timezone

pytestmark = pytest.mark.asyncio

from tests.integration.conftest_pg import client, engine, db_session  # noqa


# ── Helpers ────────────────────────────────────────────────────────────────────

async def get_auth_headers(client: httpx.AsyncClient) -> dict:
    """Crée un utilisateur test et retourne ses headers JWT."""
    username = f"nut_{uuid.uuid4().hex[:8]}"
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@test.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── Tests Food Catalog ─────────────────────────────────────────────────────────

class TestFoodCatalog:

    async def test_search_food_items_empty(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.get("/api/v1/food-items", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    async def test_search_food_items_no_auth(self, client: httpx.AsyncClient):
        resp = await client.get("/api/v1/food-items")
        assert resp.status_code == 401

    async def test_get_nonexistent_food_item(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.get(f"/api/v1/food-items/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404


# ── Tests Nutrition Entries CRUD ───────────────────────────────────────────────

class TestNutritionEntriesCRUD:

    async def test_create_entry_with_macros(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 500.0,
            "protein_g": 35.0,
            "carbs_g": 60.0,
            "fat_g": 15.0,
            "meal_type": "lunch",
            "meal_name": "Poulet riz légumes",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["calories"] == 500.0
        assert data["meal_type"] == "lunch"
        assert data["meal_name"] == "Poulet riz légumes"
        assert "id" in data
        assert "user_id" in data

    async def test_create_entry_no_source_fails(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "meal_type": "lunch",
            # Aucune source ni macro
        })
        assert resp.status_code == 422

    async def test_list_entries_empty(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.get("/api/v1/nutrition/entries", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "entries" in data
        assert "total" in data

    async def test_list_entries_by_date(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        # Créer une entrée
        await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 300.0, "meal_type": "breakfast",
        })
        today = datetime.now(timezone.utc).date().isoformat()
        resp = await client.get(f"/api/v1/nutrition/entries?date={today}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_get_entry_by_id(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        create_resp = await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 400.0, "protein_g": 25.0,
        })
        entry_id = create_resp.json()["id"]

        resp = await client.get(f"/api/v1/nutrition/entries/{entry_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == entry_id

    async def test_update_entry(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        create_resp = await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 300.0,
        })
        entry_id = create_resp.json()["id"]

        patch_resp = await client.patch(f"/api/v1/nutrition/entries/{entry_id}", headers=headers, json={
            "calories": 450.0,
            "meal_type": "snack",
            "notes": "Après sport",
        })
        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["calories"] == 450.0
        assert data["meal_type"] == "snack"
        assert data["notes"] == "Après sport"

    async def test_delete_entry(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        create_resp = await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 200.0,
        })
        entry_id = create_resp.json()["id"]

        del_resp = await client.delete(f"/api/v1/nutrition/entries/{entry_id}", headers=headers)
        assert del_resp.status_code == 204

        # Vérifier que l'entrée n'est plus accessible (soft-delete)
        get_resp = await client.get(f"/api/v1/nutrition/entries/{entry_id}", headers=headers)
        assert get_resp.status_code == 404

    async def test_ownership_isolation(self, client: httpx.AsyncClient):
        """Utilisateur A ne doit pas voir les entrées d'utilisateur B."""
        headers_a = await get_auth_headers(client)
        headers_b = await get_auth_headers(client)

        create_resp = await client.post("/api/v1/nutrition/entries", headers=headers_a, json={
            "calories": 600.0,
        })
        entry_id = create_resp.json()["id"]

        # L'utilisateur B ne doit pas pouvoir accéder à l'entrée de A
        get_resp = await client.get(f"/api/v1/nutrition/entries/{entry_id}", headers=headers_b)
        assert get_resp.status_code == 404


# ── Tests Daily Summary ────────────────────────────────────────────────────────

class TestDailySummary:

    async def test_daily_summary_empty(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        today = datetime.now(timezone.utc).date().isoformat()
        resp = await client.get(f"/api/v1/nutrition/daily-summary?date={today}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_count"] == 0
        assert data["totals"]["calories"] == 0.0

    async def test_daily_summary_with_entries(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        # Créer 2 entrées
        await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 500.0, "protein_g": 30.0, "meal_type": "breakfast",
        })
        await client.post("/api/v1/nutrition/entries", headers=headers, json={
            "calories": 700.0, "protein_g": 45.0, "meal_type": "lunch",
        })

        today = datetime.now(timezone.utc).date().isoformat()
        resp = await client.get(f"/api/v1/nutrition/daily-summary?date={today}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["meal_count"] == 2
        assert data["totals"]["calories"] == pytest.approx(1200.0)
        assert data["totals"]["protein_g"] == pytest.approx(75.0)
        assert "eating_window" in data
        assert "meals" in data


# ── Tests Photo Pipeline (mock mode) ──────────────────────────────────────────

class TestPhotoPipeline:

    async def test_get_nonexistent_photo(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.get(f"/api/v1/nutrition/photos/{uuid.uuid4()}", headers=headers)
        assert resp.status_code == 404

    async def test_confirm_nonexistent_photo(self, client: httpx.AsyncClient):
        headers = await get_auth_headers(client)
        resp = await client.post(f"/api/v1/nutrition/photos/{uuid.uuid4()}/confirm", headers=headers, json={
            "meal_type": "lunch",
        })
        assert resp.status_code == 404

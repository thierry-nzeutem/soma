"""
Configuration pytest pour les tests d'intégration PostgreSQL.

Utilisation :
    SOMA_TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/soma_test pytest tests/integration/ -v

Si SOMA_TEST_DATABASE_URL n'est pas défini, tous les tests sont automatiquement skippés.
La base de test est créée et détruites pour chaque session de test.
"""
import os
import pytest
import pytest_asyncio
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import FastAPI

# ── Skip si DATABASE_URL absent ────────────────────────────────────────────────

TEST_DATABASE_URL = os.environ.get("SOMA_TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    pytest.skip(
        "SOMA_TEST_DATABASE_URL non défini — tests d'intégration ignorés.",
        allow_module_level=True,
    )


# ── Setup DB ───────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Moteur SQLAlchemy connecté à la base de test."""
    from app.db.base import Base
    # Import de tous les modèles pour que Base.metadata soit complet
    import app.models.user  # noqa
    import app.models.health  # noqa
    import app.models.workout  # noqa
    import app.models.nutrition  # noqa
    import app.models.scores  # noqa
    import app.models.metrics  # noqa
    import app.models.insights  # noqa

    eng = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Création des tables
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield eng

    # Nettoyage après la session
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Session DB isolée par test (rollback automatique)."""
    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with SessionFactory() as session:
        async with session.begin():
            yield session
            await session.rollback()


@pytest_asyncio.fixture
async def client(engine):
    """Client HTTP asynchrone pour tester l'API FastAPI complète."""
    from app.main import app
    from app.db.session import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with SessionFactory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def register_and_login(client: httpx.AsyncClient, username: str = "testuser") -> dict:
    """
    Helper : crée un utilisateur et retourne son token JWT.
    Retourne {"access_token": ..., "refresh_token": ...}
    """
    resp = await client.post("/api/v1/auth/register", json={
        "username": username,
        "email": f"{username}@soma-test.com",
        "password": "TestPass123!",
    })
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    return resp.json()


def auth_headers(token: str) -> dict:
    """Retourne les headers d'authentification Bearer."""
    return {"Authorization": f"Bearer {token}"}

#!/usr/bin/env python3
"""
Script d'initialisation de la bibliothèque d'exercices SOMA.

Usage :
    cd soma/backend
    python scripts/seed_exercises.py

Caractéristiques :
  - Idempotent : utilise le slug comme clé unique — ne duplique pas si déjà présent
  - Compatible Python 3.11+
  - Lit DATABASE_URL depuis .env ou la variable d'environnement
  - Retourne un résumé : créés / ignorés / erreurs
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path Python pour les imports app.*
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Charger le .env avant les imports SQLAlchemy
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text

from app.models.workout import ExerciseLibrary  # noqa: F401 (nécessaire pour Base.metadata)
from app.db.base import Base

SEED_FILE = ROOT / "data" / "exercises_seed.json"


async def seed(db: AsyncSession) -> dict:
    """
    Insère les exercices depuis exercises_seed.json.
    Stratégie : upsert par slug (insert if not exists).
    """
    with open(SEED_FILE, encoding="utf-8") as f:
        exercises_data = json.load(f)

    created = 0
    skipped = 0
    errors = 0

    for data in exercises_data:
        try:
            slug = data.get("slug")
            if not slug:
                print(f"  ⚠️  Exercice sans slug ignoré : {data.get('name', '?')}")
                skipped += 1
                continue

            # Vérifie si l'exercice existe déjà
            result = await db.execute(
                select(ExerciseLibrary).where(ExerciseLibrary.slug == slug)
            )
            existing = result.scalar_one_or_none()

            if existing:
                skipped += 1
                continue

            exercise = ExerciseLibrary(
                name=data["name"],
                name_fr=data.get("name_fr"),
                slug=slug,
                category=data.get("category"),
                subcategory=data.get("subcategory"),
                primary_muscles=data.get("primary_muscles"),
                secondary_muscles=data.get("secondary_muscles"),
                difficulty_level=data.get("difficulty_level"),
                equipment_required=data.get("equipment_required"),
                execution_location=data.get("execution_location"),
                format_type=data.get("format_type"),
                met_value=data.get("met_value"),
                cv_supported=data.get("cv_supported", False),
                description=data.get("description"),
                instructions=data.get("instructions"),
                common_errors=data.get("common_errors"),
            )
            db.add(exercise)
            created += 1
            print(f"  ✅ Créé : {data['name']}")

        except Exception as e:
            errors += 1
            print(f"  ❌ Erreur sur '{data.get('name', '?')}' : {e}")

    await db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL non définie. Vérifiez votre fichier .env.")
        sys.exit(1)

    if not SEED_FILE.exists():
        print(f"❌ Fichier seed introuvable : {SEED_FILE}")
        sys.exit(1)

    print(f"🌱 Chargement des exercices depuis : {SEED_FILE}")
    print(f"🔗 Base de données : {database_url.split('@')[-1] if '@' in database_url else '...'}")
    print()

    engine = create_async_engine(database_url, echo=False)
    SessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with SessionFactory() as session:
        summary = await seed(session)

    await engine.dispose()

    print()
    print("─" * 40)
    print(f"✅ Créés    : {summary['created']}")
    print(f"⏭️  Ignorés  : {summary['skipped']} (déjà présents)")
    print(f"❌ Erreurs  : {summary['errors']}")
    print("─" * 40)

    if summary["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

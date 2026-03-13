#!/bin/bash
# Script de setup de l'environnement de développement SOMA

set -e

echo "🚀 SOMA — Setup environnement de développement"
echo "================================================"

# 1. Docker (PostgreSQL + Redis)
echo ""
echo "📦 Démarrage des services Docker..."
cd "$(dirname "$0")/../docker"
docker-compose up -d

echo "⏳ Attente des services..."
sleep 5

# 2. Backend Python
echo ""
echo "🐍 Setup backend Python..."
cd "$(dirname "$0")/../backend"

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env créé depuis .env.example"
fi

python -m pip install -r requirements.txt

# 3. Migrations Alembic
echo ""
echo "🗄️ Application des migrations..."
python -m alembic upgrade head

# 4. Tests
echo ""
echo "🧪 Lancement des tests..."
python -m pytest tests/test_calculations.py -v

echo ""
echo "✅ Setup terminé !"
echo ""
echo "Pour démarrer le backend:"
echo "  cd backend && uvicorn app.main:app --reload"
echo ""
echo "API docs: http://localhost:8000/docs"

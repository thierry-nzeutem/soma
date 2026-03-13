# SOMA — Personal Health Operating System

> Un système d'exploitation personnel de la santé, piloté par les données, l'IA et la vision par ordinateur.

## Structure du projet

```
soma/
├── docs/               # Documentation technique et fonctionnelle
├── backend/            # API Python FastAPI
├── mobile/             # Application Flutter (iOS & Android)
├── services/
│   ├── ai/             # Services IA et ML
│   └── computer_vision/ # Analyse vidéo et pose estimation
├── docker/             # Configuration Docker / Docker Compose
└── scripts/            # Scripts utilitaires
```

## Démarrage rapide

### Prérequis
- Docker & Docker Compose
- Python 3.11+
- Flutter 3.x
- Node.js (outils dev)

### Backend local
```bash
cd backend
cp .env.example .env
docker-compose up -d  # PostgreSQL + Redis
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Mobile
```bash
cd mobile
flutter pub get
flutter run
```

## Modules fonctionnels

| Module | Description | Statut |
|--------|-------------|--------|
| A | Profil utilisateur | 🔧 En cours |
| B | Intégrations santé (Apple/Google) | 📋 Planifié |
| C | Dashboard santé global | 📋 Planifié |
| D | Moteur de programmation sportive | 📋 Planifié |
| E | Bibliothèque d'exercices | 📋 Planifié |
| F | Analyse vidéo / Computer Vision | 📋 Planifié |
| G | Journal d'entraînement | 📋 Planifié |
| H | Analyse alimentation par photo | 📋 Planifié |
| I | Journal alimentaire | 📋 Planifié |
| J | Moteur nutritionnel | 📋 Planifié |
| K | Analyse micronutritionnelle | 📋 Planifié |
| L | Recommandations complémentation | 📋 Planifié |
| M | Hydratation | 📋 Planifié |
| N | Sommeil & Récupération | 📋 Planifié |
| O | Jumeau métabolique numérique | 📋 Planifié |
| P | Analyse biomécanique | 📋 Planifié |
| Q | Score longévité | 📋 Planifié |
| R | IA conseillère quotidienne | 📋 Planifié |
| S | Détection stagnation | 📋 Planifié |
| T | Prédictions futuristes | 📋 Planifié |
| U | Apprentissage personnalisé | 📋 Planifié |
| V | Notifications & Alertes | 📋 Planifié |
| W | Rapports long terme | 📋 Planifié |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Modèle de données](docs/DATA_MODEL.md)
- [Roadmap](docs/ROADMAP.md)
- [Risques](docs/RISKS.md)
- [Contrats API](docs/API_CONTRACTS.md)
- [Changelog](CHANGELOG.md)
- [TODO](TODO.md)

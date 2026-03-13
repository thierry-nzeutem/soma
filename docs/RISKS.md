# SOMA — Registre des Risques

## Risques Techniques

| ID | Risque | Impact | Probabilité | Mitigation |
|----|--------|--------|-------------|------------|
| T1 | Analyse photo repas : précision IA insuffisante | Élevé | Moyen | Toujours proposer correction manuelle + niveau confiance affiché |
| T2 | Computer vision : latence trop élevée sur mobile | Élevé | Moyen | Traitement hybride on-device (TFLite) + offload serveur selon complexité |
| T3 | Apple HealthKit : restrictions sandboxing iOS | Élevé | Faible | Prévoir import manuel export XML comme fallback |
| T4 | Fragmentation Android Health Connect | Moyen | Moyen | Abstraction commune + tests multi-devices |
| T5 | Estimation glycémie/cortisol : risque de précision trop faible | Moyen | Élevé | Présentation comme estimation qualitative uniquement, disclaimer clair |
| T6 | Sync offline : conflits de données | Moyen | Moyen | Stratégie last-write-wins avec timestamp + UI de résolution |
| T7 | Coût API LLM (Claude/GPT) pour analyse photos | Moyen | Élevé | Cache agressif, modèles locaux légers en fallback, limites quotidiennes |
| T8 | Performances PostgreSQL sur grandes séries temporelles | Moyen | Faible | Partitionnement par mois, indexes optimaux, archivage données > 1 an |

## Risques Fonctionnels

| ID | Risque | Impact | Probabilité | Mitigation |
|----|--------|--------|-------------|------------|
| F1 | Recommandations trop génériques = perte d'intérêt utilisateur | Élevé | Moyen | Personnalisation progressive, collecte feedback explicite |
| F2 | Surcharge de notifications = fatigue utilisateur | Moyen | Moyen | Throttling intelligent, configurabilité granulaire |
| F3 | Modèle TDEE incorrect → recommandations calories erronées | Élevé | Moyen | Multi-modèles (Mifflin, Katch-McArdle si composition dispo), validation continue vs poids réel |
| F4 | Jumeau métabolique : confiance utilisateur trop élevée | Moyen | Moyen | Disclaimer systématique, nature estimative très visible dans l'UI |
| F5 | Journal alimentaire fastidieux → abandon | Élevé | Moyen | Photo-first, saisie rapide, apprentissage des repas récurrents |

## Risques Données

| ID | Risque | Impact | Probabilité | Mitigation |
|----|--------|--------|-------------|------------|
| D1 | Perte de données locale si corruption SQLite | Élevé | Faible | Sync continue vers backend, backup automatique quotidien |
| D2 | Données santé sensibles non chiffrées | Très élevé | Faible | AES-256 chiffrement local, JWT sécurisé, SecureStorage mobile |
| D3 | Déduplication health samples défaillante | Moyen | Moyen | Index unique composite, pipeline de validation à l'import |

## Arbitrages techniques

| Décision | Alternative écartée | Raison |
|----------|---------------------|--------|
| Flutter (multi-plateforme) | React Native / natif séparé | Une seule codebase, meilleures perfs graphiques, excellent support caméra |
| FastAPI (Python async) | Django / Node.js | Typage fort Pydantic, async natif, performance, écosystème ML Python |
| SQLAlchemy 2.0 async | Tortoise ORM / Prisma | Maturité, flexibilité, excellent support migrations Alembic |
| PostgreSQL | SQLite / MongoDB | Richesse requêtes, extensions (pgvector, pg_trgm), ACID |
| Redis | RabbitMQ | Simplicité, cache + broker + pub-sub dans un seul service |
| MediaPipe | OpenPose / MoveNet | Support mobile natif (Dart package), performance temps réel |

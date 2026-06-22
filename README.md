# ObRail MSPR 3 - Mise en production d'une solution IA

Ce dépôt contient le chantier MSPR 3 du projet ObRail Europe. L'objectif est d'industrialiser le socle livré lors des MSPR précédentes pour produire une application complète, conteneurisée, testée, supervisée et documentée.

## Contexte

ObRail Europe est un observatoire indépendant spécialisé dans l'analyse des flux ferroviaires européens et la mobilité durable.

Le projet dispose déjà de deux briques précédentes :

- MSPR 1 : constitution et harmonisation des données ferroviaires via ETL.
- MSPR 2 : modèles prédictifs et API FastAPI prototype pour la substitution avion/train et l'estimation CO2.

La MSPR 3 vise la mise en production de l'application autour de ce socle.

## Objectifs MSPR 3

- Stabiliser le backend REST.
- Créer un frontend professionnel et accessible.
- Conteneuriser backend, frontend, base de données et monitoring.
- Mettre en place une CI/CD.
- Ajouter des tests unitaires, intégration et E2E.
- Superviser l'application avec des métriques et logs.
- Documenter l'architecture, l'installation, les tests, le monitoring, la sécurité, le RGPD et le rollback.
- Fournir une checklist finale de verification jury dans `docs/final-checklist.md`.

## Structure

```text
backend/       API FastAPI industrialisée
frontend/      Interface utilisateur ObRail
data/          Dataset harmonisé de référence
models/        Modèles prédictifs hérités de la MSPR 2
docker/        Docker Compose et configuration d'orchestration
monitoring/    Prometheus, Grafana et dashboards
docs/          Documentation technique et architecture
project/       Pilotage projet, backlog, board Trello
```

## Démarrage cible

Le livrable final devra pouvoir être lancé par :

```bash
docker compose -f docker/docker-compose.yml up --build
```

La procedure detaillee, les variables d'environnement, les volumes et les verifications post-demarrage sont documentes dans `docs/docker.md`.

## Services cibles

- Frontend : `http://localhost:5173`
- API backend : `http://localhost:8000`
- Swagger : `http://localhost:8000/docs`
- Monitoring Grafana : `http://localhost:3000`
- Prometheus : `http://localhost:9090`

## Endpoints API attendus

- `GET /health`
- `GET /trajets`
- `GET /trajets/{id}`
- `GET /stats/volumes`
- `POST /predict/substitution`
- `POST /predict/co2`

## Base de données

PostgreSQL 15 via Docker.

### Lancement
```bash
docker compose -f docker/docker-compose.yml up -d db
```

### Import des données
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
python seed.py
```

Les variables d'environnement nécessaires sont dans `backend/.env.example`.

## Traçabilité

Tout changement doit être commité avec un message explicite. Le board projet se trouve dans `project/`.

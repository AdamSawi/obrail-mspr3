# ObRail Europe — MSPR TPRE532

> Observatoire ferroviaire européen — Mise en production d'une solution IA  
> EPSI Lyon — Bachelor Développeur IA — Bloc E6.3 RNCP36581 — 2025/2026

Dépôt GitHub : https://github.com/AdamSawi/obrail-mspr3

---

## Présentation

ObRail Europe est un observatoire indépendant spécialisé dans l'analyse des flux ferroviaires européens et la promotion du transport bas-carbone. Ce projet industrialise une solution applicative complète autour d'un dataset de **142 411 trajets ferroviaires** couvrant l'Allemagne, l'Espagne, la France et l'Italie.

La solution expose une API REST FastAPI connectée à une base PostgreSQL, une interface React, des modèles IA de prédiction (substitution train/avion, régression CO2), et une supervision complète via Prometheus, Grafana et Loki.

---

## Prérequis

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé et en cours d'exécution
- Git
- Ports disponibles : 5432, 8000, 5173, 3001, 9090, 8081, 3100

---

## Lancement en une seule commande

Depuis la racine du dépôt :

```bash
docker compose -f docker/docker-compose.yml up --build
```

Cette commande :
1. Construit les images backend et frontend
2. Démarre PostgreSQL et attend qu'il soit prêt
3. Importe automatiquement les 142 411 trajets dans la base
4. Démarre l'API FastAPI
5. Démarre le frontend React
6. Démarre Prometheus, Grafana et Loki

**Première fois : prévoir 3 à 5 minutes.** Les relances suivantes démarrent en moins d'une minute.

Pour relancer sans reconstruire :

```bash
docker compose -f docker/docker-compose.yml up
```

Pour arrêter :

```bash
docker compose -f docker/docker-compose.yml down
```

---

## Services disponibles

| Service | URL | Identifiants |
|---|---|---|
| Frontend | http://localhost:5173 | — |
| API REST | http://localhost:8000 | — |
| Documentation Swagger | http://localhost:8000/docs | — |
| Grafana | http://localhost:3001 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| Adminer (PostgreSQL) | http://localhost:8081 | voir ci-dessous |

**Connexion Adminer :**
- Système : PostgreSQL
- Serveur : db
- Utilisateur : obrail
- Mot de passe : obrail
- Base de données : obrail

---

## Vérification rapide

```bash
# Santé de l'API (doit afficher status ok et rows 142411)
curl http://localhost:8000/health

# Liste des trajets (première page)
curl "http://localhost:8000/trajets?page_size=5"

# Statistiques CO2 par pays
curl http://localhost:8000/stats/volumes
```

---

## Tests automatisés

### Tests backend (Pytest)

```bash
pip install psycopg2-binary python-logging-loki
python -m pytest backend/tests/ -v
# Résultat attendu : 12 passed
```

### Tests E2E (Playwright)

Le frontend doit être démarré avant de lancer les tests E2E.

```bash
pip install playwright
playwright install chromium
python -m pytest frontend/tests/test_e2e.py -v
# Résultat attendu : 4 passed
```

---

## Structure du projet

```
obrail-mspr3/
├── backend/              API FastAPI, modèles ORM, tests Pytest
│   ├── app/
│   │   ├── main.py       Routes API, modèles IA, monitoring
│   │   ├── database.py   Connexion SQLAlchemy
│   │   └── models.py     Modèle Trip (24 colonnes)
│   ├── tests/            12 tests unitaires et d'intégration
│   └── seed.py           Import CSV → PostgreSQL
├── frontend/             Interface React/Vite
│   └── tests/            4 tests E2E Playwright
├── data/                 Dataset eu_trips_v2.csv (142 420 lignes)
├── models/               Modèles IA (.joblib)
├── docker/               docker-compose.yml (8 services)
├── monitoring/           Prometheus, Grafana, Loki, Promtail
├── scripts/              entrypoint.sh, preuve_postgresql.sh
├── .github/workflows/    Pipeline CI/CD GitHub Actions
└── RAPPORT_TECHNIQUE.md  Documentation technique complète
```

---

## Pipeline CI/CD

Le pipeline GitHub Actions se déclenche sur chaque push et pull request avec 4 jobs :

- **Backend** : installe les dépendances, seed PostgreSQL, lance Pytest
- **Frontend** : installe Node.js, lance les tests JS, build Vite
- **Docker** : valide le docker-compose et construit les images
- **E2E** : lance la stack complète et exécute les tests Playwright

---

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Pydantic |
| Base de données | PostgreSQL 15 |
| Frontend | React, Vite |
| IA | XGBoost, scikit-learn, joblib |
| Conteneurisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Monitoring | Prometheus, Grafana, Loki, Promtail |
| Tests | Pytest, Playwright |

---

## Documentation

La documentation technique complète est disponible dans [RAPPORT_TECHNIQUE.md](./RAPPORT_TECHNIQUE.md).

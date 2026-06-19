# Exigences jury MSPR 3 et preuves depot

Ce document relie les exigences attendues d'une mise en production IA aux composants presents dans le depot ObRail. Il sert de grille de lecture rapide pour la soutenance.

## Synthese finale

| Exigence MSPR 3 | Preuve ou composant repo | Etat iteration 10 | Points a annoncer au jury |
| --- | --- | --- | --- |
| API backend REST | `backend/app/main.py`, `backend/tests/` | Couverte | Routes donnees, health, predictions, erreurs homogenes et OpenAPI disponibles. |
| Predictions IA heritees MSPR 2 | `models/`, routes `/predict/substitution`, `/predict/co2` | Couverte | Les artefacts `classification_substitution_avion.joblib`, `encoders.joblib` et `regression_co2.joblib` sont versionnes ; `/health` expose leur etat. |
| Donnees harmonisees MSPR 1 | `data/eu_trips_v2.csv` | Couverte | Dataset conserve, monte en lecture seule et expose via endpoints REST. |
| Frontend utilisateur | `frontend/src/main.jsx`, `frontend/src/services/api.js` | Couverte | Dashboard React avec indicateurs, filtres, liste paginee et etat API. |
| Conteneurisation | `docker/docker-compose.yml`, Dockerfiles backend/frontend | Couverte | Commande unique Docker Compose pour backend, frontend, Prometheus et Grafana. |
| Monitoring | `backend/app/main.py`, `monitoring/`, `docs/monitoring.md` | Couverte | `/metrics`, scrape Prometheus et dashboard Grafana versionne. |
| CI/CD | `.github/workflows/ci.yml`, `docs/ci-cd.md` | Couverte | Jobs backend, frontend et Docker. |
| Tests | `backend/tests/`, `frontend/src/**/*.test.js` | Couverte pour le socle | Tests API, erreurs, CORS, metriques, services frontend et formatters. Pas encore d'E2E Playwright. |
| Documentation architecture | `README.md`, `docs/architecture.md`, `docs/technical-report.md` | Couverte | Architecture, decisions, limites, exploitation et scenario jury documentes. |
| Securite et secrets | `.gitignore`, `.dockerignore`, `docs/docker.md`, `.github/workflows/ci.yml` | Couverte pour local/jury | Aucun secret requis ; credentials Grafana par defaut reserves a la demonstration locale. |
| RGPD | `docs/technical-report.md` | Couverte au niveau demonstration | Donnees techniques ferroviaires, pas de donnees personnelles ni de tracking utilisateur. |
| Accessibilite | `frontend/src/main.jsx`, `frontend/src/styles.css`, `docs/frontend.md` | Couverte pour une base RGAA | Structure semantique, focus visible, alertes, libelles et navigation clavier de base. |
| Rollback et exploitation | `docs/technical-report.md`, `docs/docker.md` | Couverte pour local/jury | Arret, relance, nettoyage Grafana et retour revision Git documentes. |
| Checklist finale | `docs/final-checklist.md` | Couverte | Parcours de verification avant soutenance. |

## Detail par exigence

### 1. API REST exploitable

Attendu jury :

- routes documentees dans OpenAPI ;
- validation des entrees ;
- erreurs HTTP coherentes ;
- donnees exposees par endpoints REST.

Etat depot :

- FastAPI est en place dans `backend/app/main.py` ;
- `/health`, `/trajets`, `/trajets/{id}`, `/stats/volumes`, `/metrics`, `/predict/substitution` et `/predict/co2` sont exposes ;
- les erreurs controlees et les erreurs de validation utilisent une enveloppe commune `error`.

Preuves :

- `backend/tests/test_trajets.py`
- `backend/tests/test_placeholder.py`
- Swagger sur `http://localhost:8000/docs`

### 2. Modeles IA et predictions

Attendu jury :

- reutilisation du socle MSPR 2 ;
- chargement fiable ou degradation explicite des modeles ;
- messages d'erreur comprehensibles si un modele est indisponible.

Etat depot :

- `models/classification_substitution_avion.joblib`, `models/encoders.joblib` et `models/regression_co2.joblib` sont presents ;
- le backend charge le modele de classification avec ses encodeurs, ainsi que le modele de regression CO2 ;
- `/health` et `/metrics` exposent l'etat de ces dependances pour faciliter la demonstration et l'exploitation.

Decision technique :

- versionner l'artefact `models/encoders.joblib` retrouve pour rendre la classification exploitable ;
- conserver la visibilite de l'etat des modeles dans `/health` pour detecter rapidement une regression.

### 3. Donnees et tracabilite MSPR 1

Attendu jury :

- dataset conserve ;
- provenance et colonnes documentees ;
- lecture reproductible.

Etat depot :

- `data/eu_trips_v2.csv` est present et conserve ;
- le backend lit les colonnes utiles via `OBRAIL_DATASET_PATH` ;
- Docker monte `data/` en lecture seule.

Preuves :

- endpoint `/trajets` ;
- endpoint `/stats/volumes` ;
- endpoint `/health`, section `dataset`.

### 4. Frontend professionnel

Attendu jury :

- interface consultable sans competence technique ;
- acces aux indicateurs et aux trajets ;
- ergonomie et accessibilite de base.

Etat depot :

- le frontend React affiche l'etat API, les indicateurs globaux, la repartition par pays/type de train et une table paginee ;
- les filtres pays, type de train, gare de depart, gare d'arrivee et distance consomment directement `GET /trajets` ;
- les erreurs API normalisees sont affichees lisiblement.

Preuves :

- `frontend/src/main.jsx`
- `frontend/src/services/api.js`
- `frontend/src/utils/formatters.js`
- `docs/frontend.md`

### 5. Docker et orchestration

Attendu jury :

- lancement reproductible ;
- services applicatifs et monitoring ;
- documentation d'installation.

Etat depot :

- `docker/docker-compose.yml` orchestre backend, frontend, Prometheus et Grafana ;
- les donnees et modeles sont montes en lecture seule ;
- les identifiants Grafana par defaut sont limites a la demonstration locale et surchargeables par variables d'environnement.

Preuves :

- `docs/docker.md`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `.dockerignore`

### 6. Monitoring

Attendu jury :

- metriques de disponibilite, latence, erreurs et volumes ;
- visualisation Grafana ;
- documentation d'exploitation.

Etat depot :

- le backend expose `/metrics` au format Prometheus ;
- Prometheus scrape `backend:8000/metrics` ;
- Grafana provisionne une datasource Prometheus et le dashboard `ObRail API`.

Preuves :

- `docs/monitoring.md`
- `monitoring/prometheus/prometheus.yml`
- `monitoring/grafana/dashboards/obrail-api.json`

### 7. CI/CD et tests

Attendu jury :

- pipeline automatisable ;
- tests executables ;
- build reproductible.

Etat depot :

- GitHub Actions verifie backend, frontend et Docker Compose ;
- Pytest couvre les routes principales, les erreurs, CORS et Prometheus ;
- Vitest couvre les appels API frontend et les formatters.

Limites :

- aucun test E2E Playwright n'est encore versionne ;
- aucun lockfile npm n'est encore present, donc la CI frontend utilise `npm install`.

### 8. Securite, RGPD, accessibilite et rollback

Etat defendable :

- aucun secret applicatif requis pour le lancement local ;
- permissions CI limitees a `contents: read` ;
- pas de compte utilisateur ni tracking frontend ;
- donnees exposees limitees aux champs ferroviaires utiles ;
- base RGAA documentee dans `docs/frontend.md` ;
- rollback local documente dans `docs/technical-report.md`.

### 9. Limites transparentes

Les limites restantes ne doivent pas etre masquees :

- durcir la compatibilite des artefacts IA en alignant les versions `scikit-learn` d'entrainement et d'execution ;
- ajouter un lockfile npm puis passer la CI sur `npm ci` ;
- ajouter un parcours E2E Playwright ;
- ajouter un import PostgreSQL si l'equipe veut aligner totalement la cible d'architecture avec une persistance applicative ;
- completer par un audit RGAA plus formel.

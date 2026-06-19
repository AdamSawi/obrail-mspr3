# Rapport technique MSPR 3 - ObRail

## 1. Objectif du livrable

ObRail Europe est un observatoire specialise dans l'analyse des flux ferroviaires europeens et la mobilite durable.

La MSPR 3 industrialise le socle produit lors des MSPR precedentes :

- MSPR 1 : dataset ferroviaire harmonise ;
- MSPR 2 : modeles de prediction pour la substitution avion/train et l'estimation CO2 ;
- MSPR 3 : application web conteneurisee, testee, supervisee et documentee.

Le livrable vise une demonstration jury reproductible avec :

- une API REST FastAPI ;
- une interface React consultable par un utilisateur non technique ;
- des donnees et modeles montes au runtime ;
- une stack Docker Compose ;
- une supervision Prometheus/Grafana ;
- une CI GitHub Actions ;
- une documentation d'exploitation, de securite et de rollback.

Preuves principales :

- `README.md`
- `docs/architecture.md`
- `docs/docker.md`
- `docs/monitoring.md`
- `docs/ci-cd.md`
- `docs/frontend.md`
- `docs/jury-requirements.md`
- `docs/final-checklist.md`

## 2. Architecture

### 2.1 Vue logique

```text
Dataset harmonise MSPR 1
        |
        v
Backend FastAPI
        |
        v
Frontend React / Vite

Modeles MSPR 2 ----> Backend FastAPI

Backend /metrics --> Prometheus --> Grafana
CI GitHub Actions -> tests + build Docker
Docker Compose ----> orchestration locale jury
```

### 2.2 Composants applicatifs

| Composant | Role | Preuves repo |
| --- | --- | --- |
| Backend | API REST, validation, erreurs homogenes, chargement dataset, endpoints IA, metriques Prometheus | `backend/app/main.py`, `backend/tests/` |
| Frontend | Tableau de bord, filtres trajets, indicateurs, etat API | `frontend/src/main.jsx`, `frontend/src/services/api.js`, `docs/frontend.md` |
| Donnees | Dataset harmonise de reference | `data/eu_trips_v2.csv` |
| Modeles | Artefacts IA herites MSPR 2 | `models/classification_substitution_avion.joblib`, `models/regression_co2.joblib` |
| Orchestration | Lancement backend, frontend, Prometheus et Grafana | `docker/docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` |
| Monitoring | Scrape Prometheus et dashboard Grafana | `monitoring/prometheus/prometheus.yml`, `monitoring/grafana/` |
| CI/CD | Verification automatique backend, frontend et Docker | `.github/workflows/ci.yml`, `docs/ci-cd.md` |

### 2.3 Decision de persistance

L'architecture cible mentionne PostgreSQL comme option finale. L'etat actuel du livrable utilise une lecture directe du CSV harmonise via `OBRAIL_DATASET_PATH`.

Cette decision est defendable pour le rendu MSPR 3 car :

- le dataset de reference est deja harmonise ;
- le fichier est monte en lecture seule dans Docker ;
- les endpoints REST exposent un contrat stable au frontend ;
- l'ajout futur de PostgreSQL pourra se faire derriere les memes routes API.

Limite assumee : il ne s'agit pas encore d'un import applicatif complet avec historique, migrations et contraintes SQL. Ce point est identifie comme amelioration.

## 3. Choix techniques

### 3.1 Backend FastAPI

FastAPI est retenu pour :

- la generation automatique OpenAPI/Swagger ;
- la validation Pydantic des entrees ;
- la simplicite d'exposition REST ;
- la compatibilite avec les tests `TestClient`.

Endpoints principaux exposes :

- `GET /health`
- `GET /trajets`
- `GET /trajets/{id}`
- `GET /stats/volumes`
- `GET /metrics`
- `POST /predict`
- `POST /predict/substitution`
- `POST /predict/co2`

Les erreurs sont normalisees avec une enveloppe commune :

```json
{
  "error": {
    "code": "HTTP_404",
    "message": "Trajet 'unknown-trip-id' introuvable",
    "status_code": 404,
    "timestamp": "2026-06-17T10:00:00Z",
    "path": "/trajets/unknown-trip-id"
  }
}
```

Preuves :

- `backend/app/main.py`
- `backend/tests/test_trajets.py`
- `docs/monitoring.md`

### 3.2 Frontend React / Vite

Le frontend est une application monopage Vite + React.

Fonctions disponibles :

- consultation de l'etat API ;
- affichage des indicateurs globaux ;
- repartition par pays et type de train ;
- liste paginee des trajets ;
- filtres pays, type de train, origine, destination et distance ;
- gestion des erreurs backend et reseau.

Preuves :

- `frontend/src/main.jsx`
- `frontend/src/services/api.js`
- `frontend/src/utils/formatters.js`
- `docs/frontend.md`

### 3.3 Docker Compose

La commande cible est :

```bash
docker compose -f docker/docker-compose.yml up --build
```

Services exposes :

- frontend : `http://localhost:5173`
- backend : `http://localhost:8000`
- Swagger : `http://localhost:8000/docs`
- Prometheus : `http://localhost:9090`
- Grafana : `http://localhost:3000`

Les dossiers `data/` et `models/` sont montes en lecture seule dans le conteneur backend. Les artefacts volumineux ne sont pas copies dans les images.

Preuves :

- `docker/docker-compose.yml`
- `docs/docker.md`
- `.dockerignore`

## 4. Donnees et IA

### 4.1 Dataset

Le fichier `data/eu_trips_v2.csv` contient le dataset ferroviaire harmonise utilise par l'API.

Colonnes exploitees par le backend :

- identifiants : `trip_id`, `route_id`, `route_long_name` ;
- gares : `origin_stop_name`, `destination_stop_name` ;
- contexte : `country`, `type_train` ;
- mesures : `distance_km`, `duration_minutes`, `n_stops`, `kgCO2_emis` ;
- horaires : `departure_minutes`, `arrival_minutes`.

Le backend charge uniquement les colonnes utiles et met le DataFrame en cache processus avec `lru_cache`.

Preuves :

- `data/eu_trips_v2.csv`
- `backend/app/main.py`
- `backend/tests/test_trajets.py`

### 4.2 Modeles IA

Les artefacts IA sont versionnes dans `models/` :

- `classification_substitution_avion.joblib`
- `encoders.joblib`
- `regression_co2.joblib`

Le endpoint `/health` expose l'etat des modeles afin que le jury voie clairement si une dependance IA est operationnelle ou degradee.

La classification charge `models/encoders.joblib` en complement du modele de substitution avion/train. Dans Docker Compose, le dataset, la classification et la regression CO2 remontent en `ok` via `/health`.

Preuves :

- `backend/app/main.py`
- `models/`
- `docs/jury-requirements.md`

## 5. Tests et qualite

### 5.1 Backend

Tests couverts :

- pagination de `GET /trajets` ;
- filtres pays, type de train, origine et destination ;
- validation des bornes de distance ;
- enveloppe d'erreur homogene ;
- detail `GET /trajets/{id}` ;
- 404 sur identifiant inconnu ;
- agregats `GET /stats/volumes` ;
- contenu de `GET /health` ;
- CORS pour le frontend local ;
- exposition Prometheus sur `/metrics`.

Preuves :

- `backend/tests/test_trajets.py`
- `backend/tests/test_placeholder.py` pour le contrat de la route racine

Commande locale :

```bash
.venv/bin/python -m pytest -q backend/tests
```

### 5.2 Frontend

Tests couverts :

- nettoyage des filtres vides avant appel API ;
- lecture de l'enveloppe d'erreur backend ;
- construction de l'URL `/trajets` sans query string vide.

Preuves :

- `frontend/src/services/api.test.js`
- `frontend/src/utils/formatters.test.js`

Commandes attendues :

```bash
cd frontend
npm test
npm run build
```

### 5.3 CI/CD

Le workflow GitHub Actions separe trois perimetres :

- backend : installation, verification artefacts, compilation, tests Pytest ;
- frontend : installation, tests Vitest, build Vite ;
- Docker : validation Compose et build des images.

Le job Docker depend des jobs backend et frontend. Une image n'est donc construite que si les tests applicatifs passent.

Preuves :

- `.github/workflows/ci.yml`
- `docs/ci-cd.md`

## 6. Monitoring et exploitation

Le backend expose `/metrics` au format texte Prometheus.

Metriques principales :

- `obrail_api_info`
- `obrail_dependency_up`
- `obrail_dataset_rows`
- `obrail_http_requests_total`
- `obrail_http_request_duration_seconds`

Prometheus collecte le backend via `backend:8000/metrics` toutes les 15 secondes. Grafana provisionne automatiquement la datasource Prometheus et le dashboard `ObRail API`.

Requetes PromQL utiles :

```promql
sum(rate(obrail_http_requests_total[5m])) by (path)
sum(rate(obrail_http_requests_total{status=~"5.."}[5m])) by (path)
histogram_quantile(0.95, sum(rate(obrail_http_request_duration_seconds_bucket[5m])) by (le, path))
obrail_dependency_up
obrail_dataset_rows
```

Preuves :

- `backend/app/main.py`
- `monitoring/prometheus/prometheus.yml`
- `monitoring/grafana/provisioning/`
- `monitoring/grafana/dashboards/obrail-api.json`
- `docs/monitoring.md`

## 7. Securite

Mesures presentes :

- aucun secret requis pour lancer les tests ou l'application locale ;
- variables d'environnement documentees dans `docs/docker.md` ;
- CORS limite aux origines locales du frontend par defaut ;
- dossiers `data/` et `models/` montes en lecture seule dans Docker ;
- droits GitHub Actions limites a `contents: read` ;
- `.dockerignore` exclut `.git`, `.venv`, `node_modules`, `data` et `models` du contexte de build.

Points d'attention :

- les identifiants Grafana `admin/admin` sont reserves a la demonstration locale et doivent etre surcharges hors environnement jury ;
- aucun token, mot de passe ou cle API ne doit etre versionne ;
- une mise en production reelle devra ajouter HTTPS, authentification, durcissement reseau et politique de rotation des secrets.

Preuves :

- `docs/docker.md`
- `.github/workflows/ci.yml`
- `docker/docker-compose.yml`
- `.dockerignore`

## 8. RGPD

Les donnees exploitees par l'application de demonstration sont des donnees ferroviaires techniques : trajets, gares, pays, distances, durees, energie et emissions CO2.

Position RGPD pour le rendu :

- aucune donnee personnelle directe n'est exposee dans les endpoints actuels ;
- aucun compte utilisateur applicatif n'est implemente ;
- aucun tracking utilisateur n'est ajoute dans le frontend ;
- les logs applicatifs doivent rester techniques et ne pas contenir de payload sensible ;
- la minimisation est appliquee cote API en exposant uniquement les colonnes utiles au cas d'usage.

Points a formaliser en production :

- fiche de registre de traitement si le projet ajoute des utilisateurs ou des donnees partenaires nominatives ;
- duree de conservation des logs ;
- procedure de purge ;
- responsable de traitement et contacts DPO le cas echeant.

Preuves :

- `backend/app/main.py`
- `frontend/src/main.jsx`
- `data/eu_trips_v2.csv`

## 9. Accessibilite

Le frontend integre une base RGAA defendable :

- lien d'evitement vers la liste des trajets ;
- structure semantique `main`, `header`, `section`, `nav` ;
- titres hierarchises ;
- `aria-live` sur etats dynamiques ;
- `role="alert"` sur erreurs ;
- libelles explicites sur filtres ;
- focus visible ;
- tableaux avec en-tetes `scope="col"`.

Preuves :

- `frontend/src/main.jsx`
- `frontend/src/styles.css`
- `docs/frontend.md`

Limite : aucun audit RGAA automatise ou manuel complet n'est encore versionne. Une validation clavier, contraste et responsive est documentee comme verification manuelle.

## 10. Rollback

### 10.1 Rollback applicatif local

Pour revenir a une version stable :

1. arreter la stack :

```bash
docker compose -f docker/docker-compose.yml down
```

2. recuperer la revision Git stable choisie par l'equipe ;
3. relancer :

```bash
docker compose -f docker/docker-compose.yml up --build
```

### 10.2 Rollback des donnees et modeles

Les donnees et modeles ne sont pas modifies par les conteneurs car ils sont montes en lecture seule :

- `../data:/app/data:ro`
- `../models:/app/models:ro`

Le rollback consiste donc a revenir a la version Git stable des artefacts `data/` et `models/`, sans migration destructive.

### 10.3 Rollback Grafana

Pour supprimer l'etat local Grafana :

```bash
docker compose -f docker/docker-compose.yml down -v
```

Le dashboard versionne est reprovisionne depuis `monitoring/grafana/dashboards/obrail-api.json` au prochain demarrage.

Preuves :

- `docs/docker.md`
- `docker/docker-compose.yml`
- `monitoring/grafana/`

## 11. Scenario de demonstration jury

1. Lancer la stack :

```bash
docker compose -f docker/docker-compose.yml up --build
```

2. Ouvrir Swagger : `http://localhost:8000/docs`.
3. Tester `GET /health`, `GET /trajets`, `GET /stats/volumes`.
4. Ouvrir le frontend : `http://localhost:5173`.
5. Filtrer les trajets par pays, type de train et gare.
6. Ouvrir Prometheus : `http://localhost:9090/targets`.
7. Ouvrir Grafana : `http://localhost:3000`, dashboard `ObRail API`.
8. Montrer la CI : `.github/workflows/ci.yml`.
9. Montrer les tests : `backend/tests/` et `frontend/src/**/*.test.js`.

## 12. Limites et ameliorations prioritaires

| Priorite | Sujet | Justification |
| --- | --- | --- |
| 1 | Aligner les versions `scikit-learn` d'entrainement et d'execution | Eviter les avertissements de compatibilite au chargement des artefacts IA |
| 2 | Ajouter `package-lock.json` | Rendre les installations frontend reproductibles avec `npm ci` |
| 3 | Ajouter Playwright E2E | Prouver le parcours complet frontend + backend |
| 4 | Ajouter un import PostgreSQL optionnel | Aligner l'architecture cible sur une persistance applicative robuste |
| 5 | Ajouter audit accessibilite | Renforcer la defense RGAA |
| 6 | Ajouter controles statiques | Completer les tests par lint/format |
| 7 | Executer la checklist finale avant soutenance | Verifier rapidement les preuves et limites annoncees |

## 13. Synthese

Le depot presente un livrable MSPR 3 coherent pour une soutenance :

- l'API expose les donnees ferroviaires et les endpoints IA ;
- le frontend consomme les endpoints utiles ;
- Docker Compose orchestre application et monitoring ;
- Prometheus/Grafana rendent le service observable ;
- la CI automatise les controles essentiels ;
- la documentation relie les exigences jury aux fichiers du repo.

Les limites restantes sont identifiees et documentees. Elles n'empechent pas la demonstration du socle industrialise, mais constituent les prochains travaux pour une mise en production plus complete.

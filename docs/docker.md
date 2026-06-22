# Execution Docker

## Objectif

La stack Docker fournit un lancement reproductible du livrable MSPR 3 pour un evaluateur : backend FastAPI, frontend Vite, Prometheus et Grafana.

Commande cible depuis la racine du depot :

```bash
docker compose -f docker/docker-compose.yml up --build
```

## Services exposes

| Service | URL locale | Role |
| --- | --- | --- |
| PostgreSQL | `localhost:5432` | Base applicative des trajets. |
| Frontend | `http://localhost:5173` | Interface ObRail pour consulter health, indicateurs et trajets. |
| Backend | `http://localhost:8000` | API FastAPI. |
| Swagger | `http://localhost:8000/docs` | Documentation interactive de l'API. |
| Prometheus | `http://localhost:9090` | Collecte des metriques backend. |
| Grafana | `http://localhost:3000` | Dashboard `ObRail API`. |

Identifiants Grafana locaux par defaut :

- utilisateur : `admin`
- mot de passe : `admin`

Ces valeurs sont uniquement destinees a l'environnement local. Elles peuvent etre surchargees sans stocker de secret :

```bash
GRAFANA_ADMIN_USER=admin GRAFANA_ADMIN_PASSWORD='mot-de-passe-local' \
  docker compose -f docker/docker-compose.yml up --build
```

## Variables d'environnement

| Variable | Service | Valeur par defaut Compose | Description |
| --- | --- | --- | --- |
| `POSTGRES_DB` | db | `obrail` | Base PostgreSQL creee au demarrage. |
| `POSTGRES_USER` | db | `obrail` | Utilisateur applicatif local. |
| `POSTGRES_PASSWORD` | db | `obrail` | Mot de passe local de demonstration. |
| `DATABASE_URL` | backend | `postgresql://obrail:obrail@db:5432/obrail` | Connexion SQLAlchemy vers PostgreSQL. |
| `DB_HOST` | backend | `db` | Hote attendu par le script d'attente PostgreSQL. |
| `OBRAIL_DATASET_PATH` | backend | `/app/data/eu_trips_v2.csv` | Chemin du CSV harmonise dans le conteneur. |
| `OBRAIL_CORS_ORIGINS` | backend | `http://localhost:5173,http://127.0.0.1:5173` | Origines autorisees a appeler l'API depuis un navigateur. |
| `VITE_API_BASE_URL` | frontend | `http://localhost:8000` | URL publique appelee par le frontend dans le navigateur. |
| `GRAFANA_ADMIN_USER` | grafana | `admin` | Compte admin local Grafana. |
| `GRAFANA_ADMIN_PASSWORD` | grafana | `admin` | Mot de passe local, a surcharger hors demonstration locale. |

## Volumes et donnees

- `../data:/app/data:ro` expose `data/eu_trips_v2.csv` au backend sans le copier dans l'image.
- `../models:/app/models:ro` expose les modeles IA au backend sans les copier dans l'image.
- `postgres-data:/var/lib/postgresql/data` conserve la base PostgreSQL locale.
- `grafana-data:/var/lib/grafana` conserve l'etat local Grafana.
- `../monitoring/grafana/provisioning:/etc/grafana/provisioning:ro` provisionne la datasource Prometheus et le dashboard.
- `../monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro` versionne le dashboard jury.

Le fichier `.dockerignore` exclut `.venv`, `.git`, `node_modules`, `data` et `models` du contexte de build. Les donnees et modeles restent montes au runtime via les volumes ci-dessus.

Au demarrage du backend, `scripts/entrypoint.sh` attend PostgreSQL avec `pg_isready`, lance `python seed.py`, puis demarre FastAPI. Le seed est idempotent : les trajets deja presents ne sont pas reinsérés.

## Verification apres demarrage

Dans un autre terminal :

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/trajets?page_size=1"
curl http://localhost:8000/metrics
```

Dans l'interface :

1. ouvrir `http://localhost:5173` et verifier que les indicateurs et trajets se chargent ;
2. ouvrir `http://localhost:9090/targets` et verifier que la cible `obrail-backend` est `UP` ;
3. ouvrir `http://localhost:3000`, se connecter, puis ouvrir le dashboard `ObRail / ObRail API`.

## Arret et nettoyage

Arret simple :

```bash
docker compose -f docker/docker-compose.yml down
```

Arret avec suppression des volumes locaux PostgreSQL et Grafana :

```bash
docker compose -f docker/docker-compose.yml down -v
```

## Decision de persistance

La stack utilise PostgreSQL comme base applicative. Le CSV harmonise reste la source d'import : il est monte en lecture seule, puis importe dans PostgreSQL au demarrage du backend. Les routes `/trajets`, `/trajets/{id}`, `/stats/volumes` et `/health` lisent ensuite les donnees via SQLAlchemy.

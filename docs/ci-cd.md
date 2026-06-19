# CI/CD

## Objectif

Le pipeline GitHub Actions valide que le livrable MSPR 3 reste testable, constructible et exploitable avant integration.

Il couvre trois perimetres separes :

| Job | Role | Commandes principales |
| --- | --- | --- |
| `Backend - FastAPI tests` | Installer l'API, verifier les artefacts critiques et executer les tests FastAPI. | `python -m compileall backend/app`, `python -m pytest -q backend/tests` |
| `Frontend - Vite tests and build` | Installer l'interface, executer les tests Vitest et produire un build Vite. | `npm install`, `npm test`, `npm run build` |
| `Docker - Compose validation and build` | Valider le fichier Compose puis construire les images de la stack. | `docker compose -f docker/docker-compose.yml config --quiet`, `docker compose -f docker/docker-compose.yml build` |

Le job Docker depend des jobs backend et frontend. Une image n'est donc construite que si les tests applicatifs passent.

## Declencheurs

Le workflow `.github/workflows/ci.yml` s'execute sur :

- chaque `push` ;
- chaque `pull_request`.

Les permissions GitHub sont limitees a `contents: read`, car le pipeline ne publie pas d'artefact et ne modifie pas le depot.

## Backend

Le job backend utilise Python 3.12 pour rester coherent avec l'image `python:3.12-slim`.

Etapes :

1. installation des dependances depuis `backend/requirements.txt` ;
2. verification de la presence du dataset `data/eu_trips_v2.csv` ;
3. verification de la presence des modeles `models/classification_substitution_avion.joblib` et `models/regression_co2.joblib` ;
4. compilation Python rapide de `backend/app` ;
5. execution des tests `pytest`.

Cette verification protege les artefacts indispensables au scenario jury sans stocker de secret dans la CI.

## Frontend

Le job frontend utilise Node.js 22, comme le Dockerfile frontend.

Etapes :

1. installation des dependances npm ;
2. execution des tests unitaires Vitest ;
3. build Vite.

Le depot ne contient pas encore de `package-lock.json`, donc le pipeline utilise `npm install`. Des qu'un lockfile sera versionne, la commande devra etre remplacee par `npm ci` pour rendre les installations reproductibles.

## Docker

Le job Docker valide d'abord la syntaxe et la resolution de `docker/docker-compose.yml` avec `docker compose config --quiet`.

Il construit ensuite la stack Compose :

```bash
docker compose -f docker/docker-compose.yml build
```

La stack cible reste celle documentee dans `docs/docker.md` :

- backend FastAPI ;
- frontend Vite ;
- Prometheus ;
- Grafana.

## Secrets et variables

Aucun secret n'est necessaire pour la CI actuelle.

Les variables applicatives utilisees en local sont documentees dans `docs/docker.md`. Les identifiants Grafana par defaut sont reserves a la demonstration locale et peuvent etre surcharges au runtime.

## Commandes locales equivalentes

Depuis la racine du depot :

```bash
python -m pip install -r backend/requirements.txt
python -m compileall backend/app
python -m pytest -q backend/tests
```

Depuis `frontend/`, avec Node.js installe :

```bash
npm install
npm test
npm run build
```

Depuis la racine du depot, avec Docker installe :

```bash
docker compose -f docker/docker-compose.yml config --quiet
docker compose -f docker/docker-compose.yml build
```

## Prochains durcissements

- Versionner un `package-lock.json` et passer la CI frontend sur `npm ci`.
- Ajouter une verification de qualite statique si l'equipe retient un standard commun (`ruff`, `eslint` ou equivalent).
- Ajouter un test E2E Playwright quand l'interface et les donnees de demonstration seront stabilisees.
- Publier les images Docker vers un registre uniquement apres definition d'une strategie de tags et de secrets GitHub.

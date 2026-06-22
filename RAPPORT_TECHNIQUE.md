# Rapport technique MSPR 3 - ObRail Europe

## 1. Informations du rendu

Depot GitHub : https://github.com/AdamSawi/obrail-mspr3

Sujet : mise en production d'une solution applicative autour du projet ObRail Europe.

ObRail Europe est un observatoire specialise dans l'analyse des flux ferroviaires europeens et la mobilite durable. La MSPR 3 ne consiste pas a reconstruire tout le socle de donnees deja produit avant, mais a industrialiser une application complete autour de ce socle.

Le projet reprend :

- le dataset ferroviaire harmonise issu de la MSPR precedente ;
- les modeles IA deja entraines ;
- une API prototype a renforcer ;
- une application web a rendre exploitable, testable, conteneurisee et supervisee.

## 2. Objectif du projet

L'objectif est de livrer une application reproductible, capable de :

- exposer des trajets ferroviaires via une API REST ;
- afficher les donnees dans une interface web ;
- utiliser une base PostgreSQL persistante ;
- integrer les modeles IA disponibles ;
- etre lancee par Docker Compose ;
- etre verifiee par des tests automatises ;
- etre surveillee avec Prometheus, Grafana et Loki ;
- etre controlee par une pipeline CI GitHub Actions.

La solution doit pouvoir etre lancee par un evaluateur sans manipulation complexe.

Commande principale :

```bash
docker compose -f docker/docker-compose.yml up --build
```

## 3. Architecture generale

```text
Dataset harmonise MSPR precedente
        |
        v
Import reproductible seed.py
        |
        v
PostgreSQL
        |
        v
Backend FastAPI
        |
        v
Frontend React / Vite

Backend /metrics -> Prometheus -> Grafana
Logs Docker      -> Promtail   -> Loki -> Grafana
GitHub Actions   -> tests + build Docker
```

Services lances par Docker Compose :

| Service | Role | URL locale |
| --- | --- | --- |
| PostgreSQL | Base applicative persistante | `localhost:5432` |
| Backend FastAPI | API REST et endpoints IA | `http://localhost:8000` |
| Swagger | Documentation interactive API | `http://localhost:8000/docs` |
| Frontend | Interface utilisateur | `http://localhost:5173` |
| Prometheus | Collecte des metriques | `http://localhost:9090` |
| Grafana | Tableaux de bord | `http://localhost:3000` |
| Loki | Centralisation des logs | `http://localhost:3100` |

## 4. Organisation du depot

```text
backend/        API FastAPI, acces PostgreSQL, endpoints, tests
frontend/       Interface React / Vite
data/           Dataset harmonise utilise pour l'import
models/         Modeles IA versionnes
docker/         Orchestration Docker Compose
monitoring/     Configuration Prometheus, Grafana, Loki, Promtail
scripts/        Scripts de lancement et de preuve PostgreSQL
.github/        Pipeline CI GitHub Actions
project/        Elements de pilotage projet conserves hors rapport
```

Les anciens fichiers de documentation disperses ont ete regroupes dans ce rapport afin de garder un rendu plus lisible.

## 5. Donnees, ETL et PostgreSQL

Le sujet indique que le projet dispose deja d'un socle issu de la MSPR precedente : un entrepot de donnees harmonise et une API REST prototype. La MSPR 3 demande surtout d'industrialiser l'application complete.

Position retenue :

- le processus ETL complet reste rattache au socle precedent ;
- le dataset harmonise est conserve dans `data/eu_trips_v2.csv` ;
- l'application MSPR 3 importe ce dataset de maniere reproductible dans PostgreSQL ;
- les routes applicatives lisent ensuite les donnees depuis la base via SQLAlchemy.

Cette approche respecte l'objectif du sujet : avoir une application industrialisee avec une base de donnees persistante, sans refaire inutilement tout le pipeline ETL historique.

Fichiers principaux :

- `backend/seed.py` : importe le CSV dans PostgreSQL ;
- `backend/app/database.py` : configure la connexion SQLAlchemy ;
- `backend/app/models.py` : definit la table applicative `trips` ;
- `docker/docker-compose.yml` : lance PostgreSQL et le backend ;
- `scripts/entrypoint.sh` : attend PostgreSQL, lance le seed puis demarre l'API ;
- `scripts/preuve_postgresql.sh` : affiche la preuve de la base, de la table et des donnees.

Preuve observee localement :

```text
Schema | Name  | Type  | Owner
-------+-------+-------+--------
public | trips | table | obrail

nombre_de_trajets
-----------------
142411
```

La base PostgreSQL est donc presente, lancee dans Docker, et alimentee avec les trajets ferroviaires.

## 6. Backend

Le backend est developpe avec FastAPI.

Fonctions principales :

- exposition des trajets ferroviaires ;
- filtres et pagination ;
- statistiques de volumes ;
- endpoints de prediction IA ;
- route de sante applicative ;
- metriques Prometheus ;
- gestion homogene des erreurs ;
- documentation Swagger automatique.

Endpoints principaux :

```text
GET  /
GET  /health
GET  /trajets
GET  /trajets/{id}
GET  /stats/volumes
GET  /metrics
POST /predict
POST /predict/substitution
POST /predict/co2
```

Les erreurs sont renvoyees avec une structure commune, ce qui facilite le diagnostic cote frontend et monitoring.

## 7. Frontend

Le frontend est une application React avec Vite.

Il permet a un utilisateur non technique de :

- consulter l'etat de l'API ;
- voir les indicateurs principaux ;
- parcourir les trajets ;
- filtrer les donnees ;
- utiliser une interface plus accessible qu'une API brute.

Le frontend appelle le backend via la variable :

```text
VITE_API_BASE_URL=http://localhost:8000
```

## 8. Modeles IA

Les modeles sont conserves dans le dossier `models/`.

Artefacts principaux :

- `classification_substitution_avion.joblib` ;
- `regression_co2.joblib` ;
- `encoders.joblib` ;
- `scaler.joblib`.

Le endpoint `/health` indique si les dependances IA sont disponibles. Cela permet de montrer rapidement au jury si les modeles sont bien charges.

## 9. Tests et CI

La pipeline GitHub Actions se trouve dans `.github/workflows/ci.yml`.

Elle est declenchee sur :

- `push` ;
- `pull_request`.

Jobs principaux :

| Job | Role |
| --- | --- |
| Backend | installe les dependances Python, compile l'API, seed PostgreSQL et lance Pytest |
| Frontend | installe les dependances Node, lance les tests et build Vite |
| Docker | valide le fichier Compose et construit les images |

Commandes locales utiles :

```bash
python -m pip install -r backend/requirements.txt
python -m pytest -q backend/tests
```

```bash
cd frontend
npm install
npm test
npm run build
```

```bash
docker compose -f docker/docker-compose.yml config --quiet
docker compose -f docker/docker-compose.yml build
```

## 10. Monitoring et logs

Le backend expose des metriques sur :

```text
GET /metrics
```

Metriques suivies :

- disponibilite des dependances ;
- volume de donnees chargees ;
- nombre de requetes HTTP ;
- repartition des statuts HTTP ;
- temps de reponse API.

Prometheus collecte les metriques du backend. Grafana permet de les visualiser dans un tableau de bord.

Loki et Promtail sont ajoutes pour centraliser les logs Docker dans Grafana.

Fichiers principaux :

- `monitoring/prometheus/prometheus.yml` ;
- `monitoring/grafana/dashboards/obrail-api.json` ;
- `monitoring/grafana/provisioning/` ;
- `monitoring/promtail.yml`.

## 11. Securite et RGPD

Mesures deja presentes :

- aucun secret externe requis pour lancer le projet localement ;
- variables d'environnement utilisees pour la configuration ;
- CORS limite aux origines locales du frontend ;
- dataset et modeles montes en lecture seule dans Docker ;
- droits GitHub Actions limites a la lecture du depot ;
- donnees traitees de nature ferroviaire, sans donnees personnelles directes.

Points a renforcer pour une vraie production :

- HTTPS ;
- authentification ;
- politique de rotation des secrets ;
- durcissement reseau ;
- registre RGPD si des donnees personnelles sont ajoutees plus tard.

## 12. Lancement et verification jury

Depuis la racine du depot :

```bash
docker compose -f docker/docker-compose.yml up --build
```

Verifier ensuite :

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/trajets?page_size=1"
curl http://localhost:8000/stats/volumes
curl http://localhost:8000/metrics
```

Verifier PostgreSQL :

```bash
bash scripts/preuve_postgresql.sh
```

Ouvrir les interfaces :

- frontend : `http://localhost:5173` ;
- Swagger : `http://localhost:8000/docs` ;
- Prometheus : `http://localhost:9090` ;
- Grafana : `http://localhost:3000`.

Identifiants Grafana locaux :

```text
admin / admin
```

Ces identifiants sont uniquement prevus pour la demonstration locale.

## 13. Limites connues

Le projet est coherent pour une MSPR de mise en production, mais certaines limites restent a connaitre :

- l'ETL complet historique n'est pas reimplemente dans cette MSPR ;
- l'import PostgreSQL part du dataset harmonise fourni ;
- les identifiants Grafana locaux doivent etre changes hors demonstration ;
- un audit RGAA complet n'est pas encore fourni ;
- une production reelle demanderait HTTPS, authentification et durcissement supplementaire.

Ces limites sont assumables car le sujet demande surtout l'industrialisation du socle existant, pas la reconstruction complete de la chaine ETL.

## 14. Synthese

Le depot livre une solution MSPR 3 structuree autour de :

- une API FastAPI ;
- un frontend React ;
- une base PostgreSQL persistante ;
- un import reproductible des donnees ;
- des modeles IA versionnes ;
- une orchestration Docker Compose ;
- une pipeline CI ;
- une supervision Prometheus, Grafana, Loki et Promtail.

Le rendu peut etre presente comme une mise en production pedagogique du socle ObRail : l'application est executable, testable, supervisee, documentee dans ce rapport unique et reliee a son depot GitHub.

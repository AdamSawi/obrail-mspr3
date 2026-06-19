# Roadmap technique MSPR 3

Ce document organise les travaux restants pour transformer le socle ObRail en livrable MSPR 3 defendable : application lancee par Docker Compose, testee, supervisee et documentee.

## Etat de depart historique

Le depot contient deja les briques suivantes :

- `backend/` : API FastAPI avec routes de sante et predictions MSPR 2.
- `frontend/` : socle Vite React minimal.
- `data/eu_trips_v2.csv` : dataset harmonise de reference, conserve comme entree applicative.
- `models/` : modeles de classification substitution avion/train et regression CO2.
- `docker/docker-compose.yml` : orchestration backend, frontend, Prometheus et Grafana.
- `monitoring/prometheus/prometheus.yml` : configuration de collecte Prometheus.
- `.github/workflows/ci.yml` : pipeline CI initial.
- `docs/` et `project/` : documentation et pilotage projet.

Ecarts majeurs constates au demarrage des iterations, conserves ici pour tracabilite :

- resolu : les endpoints attendus `GET /trajets`, `GET /trajets/{id}` et `GET /stats/volumes` sont exposes ;
- resolu : la route `/metrics` est implementee dans le backend et collectee par Prometheus ;
- corrige : `models/encoders.joblib` a ete ajoute aux artefacts IA versionnes ;
- resolu : le frontend n'est plus un ecran de demarrage et consomme l'API ;
- choix assume : la base PostgreSQL cible n'est pas integree au compose actuel, qui lit le CSV harmonise en lecture seule ;
- resolu pour le socle : les tests backend et frontend couvrent les routes, services et formatters principaux.

## Etat final iteration 10

Les lots principaux du rendu MSPR 3 sont maintenant couverts dans le depot :

- les routes `GET /trajets`, `GET /trajets/{id}`, `GET /stats/volumes`, `GET /metrics` et les routes de prediction sont exposees ;
- le frontend React consomme l'API et presente un dashboard avec filtres, indicateurs, pagination et etat de sante ;
- Docker Compose lance backend, frontend, Prometheus et Grafana ;
- Prometheus scrape le backend et Grafana provisionne un dashboard versionne ;
- la CI execute les tests backend, les tests/build frontend et le build Docker ;
- la documentation jury est consolidee dans `docs/technical-report.md`, `docs/jury-requirements.md` et `docs/final-checklist.md`.

Ecarts restants assumes :

- la classification substitution dispose maintenant de `models/encoders.joblib` ;
- PostgreSQL reste une cible d'architecture, non integree au compose actuel ;
- un lockfile npm, un test E2E Playwright et un audit RGAA complet restent a ajouter.

## Lot 1 - Cadrage, audit et exigences

Objectif : rendre le perimetre lisible pour l'equipe et le jury.

Livrables :

- etat des lieux du depot ;
- roadmap technique ;
- matrice exigences jury vers composants du repo ;
- verification des references vers le dossier d'orchestration `docker/`.

Critere de sortie :

- la documentation permet d'expliquer ce qui existe, ce qui manque et l'ordre de realisation.

## Lot 2 - Backend API donnees

Objectif : exposer le dataset ferroviaire via des endpoints REST stables.

Travaux :

- charger `data/eu_trips_v2.csv` depuis `OBRAIL_DATASET_PATH` ;
- implementer `GET /trajets` avec pagination et filtres simples ;
- implementer `GET /trajets/{id}` sur un identifiant stable ;
- implementer `GET /stats/volumes` avec indicateurs utiles ;
- uniformiser les erreurs HTTP ;
- ajouter des tests unitaires et integration API.

Critere de sortie :

- les routes attendues par le README repondent avec donnees reelles et schemas documentes.

## Lot 3 - Predictions MSPR 2 industrialisees

Objectif : fiabiliser les routes IA existantes pour une demonstration jury.

Travaux :

- durcir le pipeline IA pour garantir la compatibilite entre versions d'entrainement et d'execution ;
- documenter les entrees, sorties et limites des modeles ;
- ajouter des tests de disponibilite et de validation payload ;
- gerer les erreurs modele avec des statuts HTTP coherents.

Critere de sortie :

- `/health` indique clairement l'etat des modeles et les routes de prediction sont testables.

## Lot 4 - Frontend ObRail

Objectif : fournir une interface institutionnelle exploitable par un utilisateur non technique.

Travaux :

- creer un tableau de bord avec indicateurs volumes et etat API ;
- creer une liste de trajets avec filtres ;
- afficher une fiche trajet ;
- integrer les appels API via une variable `VITE_API_BASE_URL` ;
- appliquer les bases RGAA : structure semantique, contrastes, navigation clavier.

Critere de sortie :

- un utilisateur peut consulter les donnees principales sans utiliser Swagger.

## Lot 5 - Conteneurisation et persistance

Objectif : livrer une execution reproductible par commande unique.

Travaux :

- consolider `docker/docker-compose.yml` ;
- ajouter PostgreSQL si retenu pour l'architecture finale ;
- documenter les variables d'environnement ;
- verifier les volumes de donnees et de monitoring ;
- ajouter une procedure de demarrage et d'arret.

Critere de sortie :

- `docker compose -f docker/docker-compose.yml up --build` demarre le livrable complet.

## Lot 6 - Monitoring et exploitation

Objectif : rendre l'application observable.

Travaux :

- exposer `/metrics` depuis le backend ;
- collecter disponibilite, latence, erreurs et volumes ;
- ajouter un dashboard Grafana versionne ;
- documenter l'exploitation et les signaux d'alerte ;
- ajouter une procedure de rollback.

Critere de sortie :

- Prometheus collecte le backend et Grafana affiche un tableau de bord lisible.

## Lot 7 - Qualite, tests et CI/CD

Objectif : securiser les evolutions et prouver la qualite du livrable.

Travaux :

- enrichir les tests backend ;
- ajouter tests frontend ;
- ajouter tests E2E Playwright si le temps le permet ;
- conserver le build Docker dans la CI ;
- documenter les commandes de verification locales et CI.

Critere de sortie :

- une modification casse moins facilement le livrable et les commandes de test sont reproductibles.

## Lot 8 - Documentation jury

Objectif : disposer d'un dossier soutenable et exploitable.

Travaux :

- completer architecture, installation, monitoring, tests, securite, RGPD, accessibilite et rollback ;
- relier chaque exigence MSPR 3 a une preuve du depot ;
- preparer un scenario de demonstration ;
- tenir a jour le board projet et les documents de suivi dans `project/`.

Critere de sortie :

- le jury peut retrouver rapidement les preuves techniques dans le repo.

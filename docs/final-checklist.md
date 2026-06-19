# Checklist finale MSPR 3

Cette checklist sert de controle avant rendu ou demonstration jury. Elle ne remplace pas le rapport technique, mais permet de verifier rapidement que le depot presente un livrable coherent.

## 1. Hygiene du depot

- [ ] Rester sur une revision Git propre ou clairement expliquee.
- [ ] Ne pas modifier ni supprimer `data/eu_trips_v2.csv`.
- [ ] Ne pas modifier ni supprimer les artefacts dans `models/`.
- [ ] Ne stocker aucun secret, token ou mot de passe personnel.
- [ ] Conserver les credentials Grafana `admin/admin` uniquement pour la demonstration locale.
- [ ] Verifier que le chantier Shopify n'est pas inclus dans le perimetre MSPR 3.

## 2. Verification backend

- [ ] Installer les dependances backend si necessaire : `python -m pip install -r backend/requirements.txt`.
- [ ] Compiler le backend : `python -m compileall backend/app`.
- [ ] Executer les tests : `python -m pytest -q backend/tests`.
- [ ] Lancer l'API et verifier `GET /health`.
- [ ] Verifier `GET /trajets?page_size=1`.
- [ ] Verifier `GET /stats/volumes`.
- [ ] Verifier `GET /metrics`.
- [ ] Ouvrir Swagger sur `http://localhost:8000/docs`.

## 3. Verification frontend

- [ ] Installer les dependances depuis `frontend/` : `npm install`.
- [ ] Executer les tests : `npm test`.
- [ ] Construire l'application : `npm run build`.
- [ ] Verifier que `VITE_API_BASE_URL` pointe vers le backend attendu.
- [ ] Tester manuellement les filtres pays, type de train, gares et distances.
- [ ] Tester la navigation clavier de base, le focus visible et le lien d'evitement.
- [ ] Verifier l'affichage en largeur mobile et desktop.

## 4. Verification Docker

- [ ] Valider Compose : `docker compose -f docker/docker-compose.yml config --quiet`.
- [ ] Lancer la stack : `docker compose -f docker/docker-compose.yml up --build`.
- [ ] Ouvrir le frontend : `http://localhost:5173`.
- [ ] Ouvrir l'API : `http://localhost:8000/health`.
- [ ] Ouvrir Prometheus : `http://localhost:9090/targets`.
- [ ] Ouvrir Grafana : `http://localhost:3000`.
- [ ] Verifier que le dashboard `ObRail API` est provisionne.
- [ ] Arreter proprement : `docker compose -f docker/docker-compose.yml down`.

## 5. Verification monitoring

- [ ] Confirmer que la cible Prometheus `obrail-backend` est `UP`.
- [ ] Confirmer que `/metrics` contient `obrail_api_info`.
- [ ] Confirmer que `/metrics` contient `obrail_dependency_up`.
- [ ] Confirmer que `/metrics` contient `obrail_http_requests_total`.
- [ ] Confirmer que `/metrics` contient `obrail_http_request_duration_seconds`.
- [ ] Confirmer que `/metrics` contient `obrail_dataset_rows`.
- [ ] Dans Grafana, verifier au moins disponibilite, latence, erreurs et volume dataset.

## 6. Verification CI/CD

- [ ] Relire `.github/workflows/ci.yml`.
- [ ] Verifier que le job backend installe, compile et teste l'API.
- [ ] Verifier que le job frontend teste et build Vite.
- [ ] Verifier que le job Docker valide et construit Compose.
- [ ] Confirmer qu'aucun secret GitHub n'est requis pour le pipeline actuel.

## 7. Preuves jury a ouvrir

- [ ] `README.md` pour le contexte et les endpoints.
- [ ] `docs/architecture.md` pour la vue logique.
- [ ] `docs/docker.md` pour le lancement.
- [ ] `docs/frontend.md` pour le parcours utilisateur et l'accessibilite.
- [ ] `docs/monitoring.md` pour Prometheus/Grafana.
- [ ] `docs/ci-cd.md` pour le pipeline.
- [ ] `docs/jury-requirements.md` pour la matrice exigences/preuves.
- [ ] `docs/technical-report.md` pour la synthese complete, securite, RGPD et rollback.

## 8. Limites a annoncer clairement

- [ ] `models/encoders.joblib` est present avec les artefacts IA.
- [ ] Dans Docker Compose, `/health` remonte le dataset, la classification substitution et la regression CO2 en `ok`.
- [ ] Le frontend n'a pas encore de test E2E Playwright.
- [ ] Le frontend n'a pas encore de `package-lock.json`.
- [ ] PostgreSQL reste une option cible, non integree dans la stack actuelle.
- [ ] Aucun audit RGAA complet n'est versionne.

## 9. Scenario court de demonstration

1. Lancer `docker compose -f docker/docker-compose.yml up --build`.
2. Montrer `http://localhost:8000/docs`, puis executer `/health`, `/trajets` et `/stats/volumes`.
3. Montrer `http://localhost:5173`, filtrer quelques trajets et commenter les indicateurs.
4. Montrer `http://localhost:9090/targets` avec le backend `UP`.
5. Montrer Grafana et le dashboard `ObRail API`.
6. Montrer `.github/workflows/ci.yml` et les tests backend/frontend.
7. Ouvrir `docs/jury-requirements.md` pour relier les preuves aux exigences.

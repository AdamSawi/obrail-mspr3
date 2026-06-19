# Board Trello - ObRail MSPR 3

## Colonnes

- Backlog
- A faire
- En cours
- Review
- Termine
- Bloque

## Backlog initial

### Cadrage et architecture

- Valider le périmètre MSPR 3 avec l'équipe
- Rédiger l'architecture cible
- Identifier les composants hérités MSPR 1 et MSPR 2
- Définir les responsabilités par membre
- Lister les risques techniques

### Backend

- Stabiliser l'API FastAPI existante
- Ajouter `GET /trajets`
- Ajouter `GET /trajets/{id}`
- Ajouter `GET /stats/volumes`
- Renforcer `GET /health`
- Ajouter gestion d'erreurs HTTP homogène
- Ajouter documentation OpenAPI propre
- Ajouter métriques `/metrics`

### ETL et données

- Documenter la provenance du dataset harmonisé
- Créer un script d'import reproductible
- Valider les colonnes nécessaires
- Préparer une stratégie de persistance
- Ajouter tests sur l'import

### Frontend

- Créer le socle frontend
- Construire la page tableau de bord
- Construire la liste des trajets
- Ajouter filtres pays, type de train, distance
- Afficher les indicateurs clés
- Afficher l'état de santé API
- Vérifier accessibilité RGAA de base

### Docker et orchestration

- Dockerfile backend
- Dockerfile frontend
- Docker Compose complet
- Volumes de persistance
- Variables d'environnement documentées
- Commande unique de lancement

### Tests

- Tests unitaires backend
- Tests intégration API/données
- Tests frontend
- Tests E2E Playwright
- Documentation d'exécution des tests

### CI/CD

- Workflow GitHub Actions
- Installation dépendances backend
- Installation dépendances frontend
- Exécution tests automatiques
- Build Docker Compose
- Documentation secrets et variables

### Monitoring

- Ajouter Prometheus
- Ajouter Grafana
- Exposer métriques backend
- Dashboard disponibilité API
- Dashboard latence et erreurs
- Documentation exploitation

### Rapport et soutenance

- Rapport technique
- Schémas architecture
- Procédure installation
- Procédure rollback
- Section RGPD
- Section sécurité
- Section accessibilité
- Support oral

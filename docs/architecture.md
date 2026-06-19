# Architecture cible MSPR 3

## Vue logique

```text
Sources ferroviaires / ETL MSPR 1
        |
        v
Dataset harmonisé / import base
        |
        v
Base de données applicative
        |
        v
Backend FastAPI
        |
        v
Frontend ObRail
```

Autour de l'application :

```text
CI/CD -> tests -> build Docker -> version testable
Monitoring -> métriques API -> logs -> dashboard Grafana
Documentation -> installation -> exploitation -> rollback
```

## Composants

### Backend

Le backend expose les données ferroviaires harmonisées et conserve les routes de prédiction héritées de la MSPR 2.

Responsabilités :

- routes `/trajets`, `/trajets/{id}`, `/stats/volumes`, `/health` ;
- validation des entrées ;
- erreurs HTTP maîtrisées ;
- documentation OpenAPI ;
- métriques Prometheus ;
- accès base de données.

### Frontend

Le frontend permet à un utilisateur institutionnel ou partenaire de consulter les données sans compétence technique.

Fonctionnalités attendues :

- liste et filtres de trajets ;
- indicateurs jour/nuit, pays, opérateurs ou volumes ;
- état de santé de l'API ;
- respect des principes d'accessibilité RGAA.

### ETL / Import

L'ETL complet appartient au socle précédent. Pour la MSPR 3, il doit rester rejouable ou documenté. Le projet inclura au minimum un import reproductible du dataset harmonisé vers la base applicative.

### Monitoring

Métriques attendues :

- disponibilité API ;
- latence ;
- taux d'erreurs ;
- volumes de données ;
- logs applicatifs.

### CI/CD

Le pipeline doit exécuter :

- installation des dépendances ;
- tests backend ;
- tests frontend ;
- build Docker ;
- vérification qualité si applicable.

## Décisions initiales

- Backend : FastAPI.
- Frontend : à confirmer selon l'équipe, recommandé Vite + React.
- Base : PostgreSQL pour l'architecture finale, SQLite possible pour tests locaux rapides.
- Monitoring : Prometheus + Grafana.
- Orchestration : Docker Compose.


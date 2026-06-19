# Monitoring

La MSPR 3 demande une supervision de l'application : disponibilité API, latence, erreurs, logs et volumes.

## Prometheus

Prometheus est l'outil qui collecte les métriques.

Dans notre architecture, il interroge le backend sur la route `/metrics`.
La configuration se trouve dans `monitoring/prometheus/prometheus.yml` :

- job Prometheus : `obrail-backend` ;
- endpoint scrape : `backend:8000/metrics` dans Docker Compose ;
- intervalle de collecte : `15s`.

La route `/metrics` expose un format texte compatible Prometheus sans dépendance applicative supplémentaire. Elle permet de vérifier les points suivants :

- nombre de requêtes HTTP ;
- temps de réponse ;
- nombre d'erreurs ;
- état du service ;
- volumes de données exposés.

### Métriques exposées par le backend

| Métrique | Type | Labels | Utilisation |
| --- | --- | --- | --- |
| `obrail_api_info` | gauge | `app`, `version` | Vérifier l'identité et la version exposée par le backend. |
| `obrail_dependency_up` | gauge | `dependency` | Suivre la disponibilité du dataset et des modèles IA (`1` disponible, `0` indisponible). |
| `obrail_dataset_rows` | gauge | aucun | Contrôler le volume de lignes chargées depuis `data/eu_trips_v2.csv`. |
| `obrail_http_requests_total` | counter | `method`, `path`, `status` | Compter les requêtes par méthode, route normalisée et statut HTTP. |
| `obrail_http_request_duration_seconds` | histogram | `method`, `path`, `le` | Mesurer la latence API par route avec buckets Prometheus. |

Exemple de vérification locale :

```bash
curl http://localhost:8000/metrics
```

Exemples de requêtes PromQL utiles pour un tableau de bord jury :

```promql
sum(rate(obrail_http_requests_total[5m])) by (path)
sum(rate(obrail_http_requests_total{status=~"5.."}[5m])) by (path)
histogram_quantile(0.95, sum(rate(obrail_http_request_duration_seconds_bucket[5m])) by (le, path))
obrail_dependency_up
obrail_dataset_rows
```

### Format d'erreurs API

Les erreurs HTTP sont normalisées pour faciliter l'exploitation par le frontend et les logs.
Une erreur contrôlée ou de validation retourne une enveloppe commune :

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

Ce format rend plus simple le suivi des erreurs dans Grafana, car le statut HTTP est aussi présent dans `obrail_http_requests_total`.

## Grafana

Grafana est l'outil qui affiche ces métriques dans un tableau de bord.

Il permet au jury ou à une équipe interne ObRail de visualiser :

- si l'API est disponible ;
- si les réponses deviennent lentes ;
- si le taux d'erreur augmente ;
- si les volumes de données sont cohérents.

La stack Docker provisionne automatiquement :

- la datasource Prometheus via `monitoring/grafana/provisioning/datasources/prometheus.yml` ;
- le dashboard `ObRail API` via `monitoring/grafana/dashboards/obrail-api.json`.

Apres lancement avec `docker compose -f docker/docker-compose.yml up --build`, le dashboard est accessible dans Grafana sur `http://localhost:3000`.

## Pourquoi garder ces dossiers

Ces dossiers ne sont pas du code métier, mais ils répondent directement à l'exigence MSPR 3 : livrer une solution supervisée et exploitable en production.

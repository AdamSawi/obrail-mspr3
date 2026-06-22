"""
api.py — API commune ObRail Europe
Démarrage : uvicorn api:app --reload
Documentation : http://localhost:8000/docs

Routes exposées :
    GET  /               → message d'accueil
    GET  /health         → statut de l'API et des modèles chargés
    GET  /trajets        → liste paginée et filtrable des trajets
    GET  /trajets/{id}   → détail d'un trajet par identifiant stable
    GET  /stats/volumes  → volumes agrégés du dataset
    POST /predict                  → classification substitution (compat. v1)
    POST /predict/substitution     → classification substitution avion/train
    POST /predict/co2              → régression émissions CO2 futures

Monitoring en production (à brancher sur Prometheus / Evidently) :
    - Taux de requêtes par minute par route
    - Distribution des prédictions dans le temps
      (proportion de 1 sur /predict/substitution, moyenne kgCO2 sur /predict/co2)
    - Data drift : comparer les distributions des features en entrée
      vs. les distributions du jeu d'entraînement à l'aide d'Evidently ou WhyLogs
    - Latence P50 / P95 / P99 par route
    - Taux d'erreurs HTTP 422 (payload invalide) et 500 (erreur modèle)
"""

from collections import defaultdict
from functools import lru_cache
from math import ceil
import logging
import os
from pathlib import Path
from time import perf_counter
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models import Trip

import logging_loki

handler = logging_loki.LokiHandler(
    url="http://loki:3100/loki/api/v1/push",
    tags={"application": "obrail-api"},
    version="1",
)

# Appliquer sur tous les loggers concernés
for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
    logging.getLogger(logger_name).addHandler(handler)

BASE_DIR = Path(__file__).resolve().parents[2]
TRIPS_CSV_PATH = Path(os.getenv("OBRAIL_DATASET_PATH", BASE_DIR / "data" / "eu_trips_v2.csv"))
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("OBRAIL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ObRail Europe — API de prédiction ferroviaire",
    description=(
        "API REST du projet ObRail Europe. "
        "Deux enjeux exposés :\n\n"
        "- **Substitution avion/train** : classification binaire — la liaison "
        "est-elle candidate à remplacer un vol aérien ?\n"
        "- **Émissions CO2 futures** : régression — estimation des émissions "
        "kgCO2 selon un scénario de développement du réseau."
    ),
    version="2.0.0",
    contact={"name": "ObRail Europe", "email": "data@obrail.eu"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Observabilité HTTP
# ---------------------------------------------------------------------------

_LATENCY_BUCKETS_SECONDS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
_REQUESTS_TOTAL: dict[tuple[str, str, int], int] = defaultdict(int)
_REQUEST_DURATION_SUM: dict[tuple[str, str], float] = defaultdict(float)
_REQUEST_DURATION_COUNT: dict[tuple[str, str], int] = defaultdict(int)
_REQUEST_DURATION_BUCKETS: dict[tuple[str, str, float], int] = defaultdict(int)


def _route_template(request: Request) -> str:
    """Retourne le template de route pour limiter la cardinalité Prometheus."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


def _record_http_metric(request: Request, status_code: int, duration_seconds: float) -> None:
    """Mémorise les métriques HTTP exposées ensuite au format Prometheus."""
    method = request.method
    path = _route_template(request)
    _REQUESTS_TOTAL[(method, path, status_code)] += 1
    _REQUEST_DURATION_SUM[(method, path)] += duration_seconds
    _REQUEST_DURATION_COUNT[(method, path)] += 1
    for bucket in _LATENCY_BUCKETS_SECONDS:
        if duration_seconds <= bucket:
            _REQUEST_DURATION_BUCKETS[(method, path, bucket)] += 1


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Mesure le volume, la latence et le statut HTTP de chaque requête."""
    start = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_seconds = perf_counter() - start
        _record_http_metric(request, status_code, duration_seconds)


def _prometheus_escape(value: str) -> str:
    """Échappe une valeur de label Prometheus."""
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _format_labels(labels: dict[str, str]) -> str:
    return ",".join(f'{key}="{_prometheus_escape(value)}"' for key, value in labels.items())


def _format_sample(metric_name: str, labels: dict[str, str], value: float | int) -> str:
    return f"{metric_name}{{{_format_labels(labels)}}} {value}"


def _dependency_metrics_lines() -> list[str]:
    """Expose l'état des dépendances critiques sous forme de gauges."""
    db = SessionLocal()
    try:
        dataset = _dataset_health(db)
    finally:
        db.close()
    dependencies = {
        "dataset": dataset["status"] == "ok",
        "classification_substitution": _substitution_ok,
        "regression_co2": _co2_ok,
    }

    lines = [
        "# HELP obrail_dependency_up Dependency availability, 1 for available and 0 for unavailable.",
        "# TYPE obrail_dependency_up gauge",
    ]
    for dependency, available in dependencies.items():
        lines.append(
            _format_sample(
                "obrail_dependency_up",
                {"dependency": dependency},
                1 if available else 0,
            )
        )

    if dataset.get("rows") is not None:
        lines.extend(
            [
                "# HELP obrail_dataset_rows Number of rows loaded from the harmonized trips dataset.",
                "# TYPE obrail_dataset_rows gauge",
                f"obrail_dataset_rows {dataset['rows']}",
            ]
        )

    return lines


def _http_metrics_lines() -> list[str]:
    """Expose les compteurs et histogrammes HTTP au format Prometheus."""
    lines = [
        "# HELP obrail_http_requests_total Total HTTP requests handled by the API.",
        "# TYPE obrail_http_requests_total counter",
    ]
    for (method, path, status_code), count in sorted(_REQUESTS_TOTAL.items()):
        lines.append(
            _format_sample(
                "obrail_http_requests_total",
                {"method": method, "path": path, "status": str(status_code)},
                count,
            )
        )

    lines.extend(
        [
            "# HELP obrail_http_request_duration_seconds HTTP request latency in seconds.",
            "# TYPE obrail_http_request_duration_seconds histogram",
        ]
    )
    for method, path in sorted(_REQUEST_DURATION_COUNT):
        cumulative = 0
        for bucket in _LATENCY_BUCKETS_SECONDS:
            cumulative = _REQUEST_DURATION_BUCKETS.get((method, path, bucket), cumulative)
            lines.append(
                _format_sample(
                    "obrail_http_request_duration_seconds_bucket",
                    {"method": method, "path": path, "le": str(bucket)},
                    cumulative,
                )
            )
        lines.append(
            _format_sample(
                "obrail_http_request_duration_seconds_bucket",
                {"method": method, "path": path, "le": "+Inf"},
                _REQUEST_DURATION_COUNT[(method, path)],
            )
        )
        lines.append(
            _format_sample(
                "obrail_http_request_duration_seconds_count",
                {"method": method, "path": path},
                _REQUEST_DURATION_COUNT[(method, path)],
            )
        )
        lines.append(
            _format_sample(
                "obrail_http_request_duration_seconds_sum",
                {"method": method, "path": path},
                round(_REQUEST_DURATION_SUM[(method, path)], 6),
            )
        )

    return lines


def _error_payload(
    *,
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details=None,
) -> dict:
    """Construit le format d'erreur homogène de l'API."""
    payload = {
        "error": {
            "code": code,
            "message": message,
            "status_code": status_code,
            "timestamp": _utc_now_iso(),
            "path": request.url.path,
        }
    }
    if details is not None:
        payload["error"]["details"] = details
    return payload


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Normalise les erreurs HTTP contrôlées."""
    detail = exc.detail if getattr(exc, "detail", None) else "Erreur HTTP"
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(
            request=request,
            status_code=exc.status_code,
            code=f"HTTP_{exc.status_code}",
            message=str(detail),
        ),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Normalise les erreurs de validation FastAPI/Pydantic."""
    return JSONResponse(
        status_code=422,
        content=_error_payload(
            request=request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Paramètres ou payload invalides",
            details=jsonable_encoder(exc.errors()),
        ),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Évite les réponses hétérogènes en cas d'erreur inattendue."""
    return JSONResponse(
        status_code=500,
        content=_error_payload(
            request=request,
            status_code=500,
            code="INTERNAL_SERVER_ERROR",
            message="Erreur interne du serveur",
        ),
    )

# ---------------------------------------------------------------------------
# Chargement des modèles au démarrage (une seule fois)
# ---------------------------------------------------------------------------

try:
    _model_substitution = joblib.load("models/classification_substitution_avion.joblib")
    _encoders = joblib.load("models/encoders.joblib")
    # StandardScaler fitted on the same 7 features (distance_km, duration_minutes,
    # n_stops, co2_estime, consommation_totale, type_train, country) used to train
    # the classification model — must be applied before predict() / predict_proba().
    _scaler = joblib.load("models/scaler.joblib")
    _substitution_ok = True
except Exception as e:
    _substitution_ok = False
    _substitution_error = str(e)

try:
    # Pipeline complet sklearn (ColumnTransformer + XGBoost) — pas d'encodeur séparé
    _model_co2 = joblib.load("models/regression_co2.joblib")
    _co2_ok = True
except Exception as e:
    _co2_ok = False
    _co2_error = str(e)

# ---------------------------------------------------------------------------
# Schémas Pydantic — Classification substitution
# ---------------------------------------------------------------------------

class LiaisonSubstitutionInput(BaseModel):
    """Caractéristiques d'une liaison ferroviaire pour la classification substitution."""

    distance_km: float = Field(
        ..., example=1200.0,
        description="Distance géographique de la liaison en km"
    )
    duration_minutes: float = Field(
        ..., example=360.0,
        description="Durée du trajet en minutes"
    )
    n_stops: int = Field(
        ..., example=2,
        description="Nombre d'arrêts intermédiaires"
    )
    co2_estime: float = Field(
        ..., example=450000.0,
        description="Émissions CO2 estimées en gCO2"
    )
    consommation_totale: float = Field(
        ..., example=20000.0,
        description="Consommation énergétique totale en kWh"
    )
    type_train: str = Field(
        ..., example="electric",
        description="Type de traction : 'electric' ou 'diesel'"
    )
    country: str = Field(
        ..., example="FR",
        description="Code pays : 'FR', 'ES', 'IT' ou 'DE'"
    )


class SubstitutionOutput(BaseModel):
    """Résultat de la classification substitution avion/train."""

    substitution_avion: int = Field(description="1 = substituable, 0 = non substituable")
    probabilite: float = Field(description="Probabilité d'être substituable (entre 0 et 1)")
    label: str = Field(description="Libellé lisible de la prédiction")


# ---------------------------------------------------------------------------
# Schémas Pydantic — Régression CO2
# ---------------------------------------------------------------------------

class LiaisonCO2Input(BaseModel):
    """Caractéristiques d'une liaison ferroviaire et scénario pour l'estimation CO2."""

    distance_km: float = Field(
        ..., example=400.0,
        description="Distance géographique de la liaison en km"
    )
    duration_minutes: float = Field(
        ..., example=120.0,
        description="Durée du trajet en minutes"
    )
    n_stops: int = Field(
        ..., example=2,
        description="Nombre d'arrêts intermédiaires"
    )
    consommation_energy: float = Field(
        ..., example=10.0,
        description="Consommation énergétique en kWh/km"
    )
    gco2_per_kwh: float = Field(
        ..., example=21.7,
        description="Facteur carbone du pays en gCO2/kWh"
    )
    consommation_totale: float = Field(
        ..., example=4000.0,
        description="Consommation totale actuelle en kWh"
    )
    type_train: str = Field(
        ..., example="diesel",
        description="Type de traction : 'electric' ou 'diesel'"
    )
    scenario: str = Field(
        ..., example="diesel_50_electrique",
        description=(
            "Scénario de développement du réseau. "
            "Valeurs : 'reference', 'diesel_50_electrique', "
            "'conso_moins_15', 'distance_moins_10'"
        )
    )


class CO2Output(BaseModel):
    """Résultat de l'estimation des émissions CO2 futures."""

    scenario: str = Field(description="Scénario appliqué")
    co2_estime_kg: float = Field(description="Émissions CO2 estimées en kgCO2")
    label: str = Field(description="Libellé lisible du résultat")


# ---------------------------------------------------------------------------
# Schémas Pydantic — Consultation des trajets
# ---------------------------------------------------------------------------

class TrajetOutput(BaseModel):
    """Trajet ferroviaire harmonisé exposé par l'API."""

    id: str = Field(description="Identifiant unique du trajet, issu de trip_id")
    route_id: str = Field(description="Identifiant de la ligne ou route")
    route_long_name: Optional[str] = Field(default=None, description="Nom commercial de la ligne")
    origin_stop_name: str = Field(description="Gare de départ")
    destination_stop_name: str = Field(description="Gare d'arrivée")
    country: str = Field(description="Code pays ISO du trajet")
    type_train: str = Field(description="Type de traction du train")
    distance_km: float = Field(description="Distance du trajet en kilomètres")
    duration_minutes: float = Field(description="Durée du trajet en minutes")
    n_stops: int = Field(description="Nombre d'arrêts intermédiaires")
    departure_minutes: Optional[float] = Field(default=None, description="Départ en minutes depuis minuit")
    arrival_minutes: Optional[float] = Field(default=None, description="Arrivée en minutes depuis minuit")
    kg_co2_emis: Optional[float] = Field(default=None, description="Émissions estimées en kgCO2")


class TrajetsResponse(BaseModel):
    """Réponse paginée de la liste des trajets."""

    page: int = Field(description="Page courante, indexée à partir de 1")
    page_size: int = Field(description="Nombre maximum de trajets retournés")
    total: int = Field(description="Nombre total de trajets après filtrage")
    total_pages: int = Field(description="Nombre total de pages après filtrage")
    items: list[TrajetOutput] = Field(description="Trajets de la page demandée")


class VolumeBucket(BaseModel):
    """Agrégat de volume pour une dimension métier."""

    key: str = Field(description="Valeur de regroupement, par exemple FR ou electric")
    total_trajets: int = Field(description="Nombre de trajets du groupe")
    total_distance_km: float = Field(description="Distance cumulée en kilomètres")
    total_kg_co2_emis: float = Field(description="Émissions cumulées en kgCO2")


class StatsVolumesResponse(BaseModel):
    """Indicateurs de volumes exposés au tableau de bord."""

    generated_at: str = Field(description="Timestamp UTC de génération")
    total_trajets: int = Field(description="Nombre total de trajets dans le dataset")
    total_countries: int = Field(description="Nombre de pays représentés")
    total_routes: int = Field(description="Nombre de routes distinctes")
    total_distance_km: float = Field(description="Distance cumulée en kilomètres")
    total_kg_co2_emis: float = Field(description="Émissions cumulées en kgCO2")
    by_country: list[VolumeBucket] = Field(description="Volumes agrégés par pays")
    by_type_train: list[VolumeBucket] = Field(description="Volumes agrégés par type de train")


# ---------------------------------------------------------------------------
# Utilitaires internes
# ---------------------------------------------------------------------------

def _build_substitution_df(liaison: LiaisonSubstitutionInput) -> pd.DataFrame:
    """Encode et construit le DataFrame d'entrée pour le modèle de classification."""
    type_train_enc = _encoders["le_type_train"].transform([liaison.type_train])[0]
    country_enc = _encoders["le_country"].transform([liaison.country])[0]
    return pd.DataFrame([{
        "distance_km":        liaison.distance_km,
        "duration_minutes":   liaison.duration_minutes,
        "n_stops":            liaison.n_stops,
        "co2_estime":         liaison.co2_estime,
        "consommation_totale": liaison.consommation_totale,
        "type_train":         type_train_enc,
        "country":            country_enc,
    }])


def _build_co2_df(liaison: LiaisonCO2Input) -> pd.DataFrame:
    """Calcule les features dérivées et construit le DataFrame pour le Pipeline CO2."""
    # Features dérivées (identiques à predict_co2.py)
    vitesse = (liaison.distance_km / (liaison.duration_minutes / 60)
               if liaison.duration_minutes > 0 else 0.0)
    co2_par_km = ((liaison.consommation_energy * liaison.gco2_per_kwh) / liaison.distance_km
                  if liaison.distance_km > 0 else 0.0)
    is_diesel   = 1 if liaison.type_train == "diesel" else 0
    is_electric = 1 if liaison.type_train == "electric" else 0

    # Adaptation selon le scénario
    distance_scenario_km  = liaison.distance_km
    consommation_scenario = liaison.consommation_totale

    if liaison.scenario == "diesel_50_electrique" and liaison.type_train == "diesel":
        consommation_scenario *= 0.50
    elif liaison.scenario == "conso_moins_15":
        consommation_scenario *= 0.85
    elif liaison.scenario == "distance_moins_10":
        distance_scenario_km  *= 0.90
        consommation_scenario *= 0.90
    # "reference" : aucune modification

    return pd.DataFrame([{
        "distance_scenario_km":  distance_scenario_km,
        "duration_minutes":      liaison.duration_minutes,
        "n_stops":               liaison.n_stops,
        "consommation_energy":   liaison.consommation_energy,
        "gco2_per_kwh":          liaison.gco2_per_kwh,
        "consommation_scenario": consommation_scenario,
        "vitesse_moyenne_kmh":   vitesse,
        "co2_par_km":            co2_par_km,
        "is_diesel":             is_diesel,
        "is_electric":           is_electric,
        "type_train":            liaison.type_train,
        "scenario":              liaison.scenario,
    }])


@lru_cache(maxsize=1)
def _load_trips_df() -> pd.DataFrame:
    """Charge le dataset harmonisé des trajets une seule fois par processus."""
    if not TRIPS_CSV_PATH.exists():
        raise FileNotFoundError(f"Dataset introuvable : {TRIPS_CSV_PATH}")

    required_columns = [
        "arrival_minutes",
        "departure_minutes",
        "destination_stop_name",
        "duration_minutes",
        "n_stops",
        "origin_stop_name",
        "route_id",
        "route_long_name",
        "trip_id",
        "country",
        "distance_km",
        "type_train",
    ]
    header = pd.read_csv(TRIPS_CSV_PATH, nrows=0).columns
    co2_column = "kgCO2_emis" if "kgCO2_emis" in header else "co2_estime"
    if co2_column not in header:
        raise ValueError("Dataset invalide : colonne CO2 attendue absente (kgCO2_emis ou co2_estime)")

    trips = pd.read_csv(TRIPS_CSV_PATH, usecols=[*required_columns, co2_column], low_memory=False)
    if co2_column != "kgCO2_emis":
        trips = trips.rename(columns={co2_column: "kgCO2_emis"})
    return trips


def _load_trips_from_db(db: Session) -> pd.DataFrame:
    """Load trips from PostgreSQL.
    Converts co2_estime (gCO2) to kgCO2_emis (kgCO2) by dividing by 1000.
    """
    rows = db.query(Trip).all()
    data = [{
        "trip_id": row.trip_id,
        "route_id": row.route_id,
        "route_long_name": row.route_long_name,
        "country": row.country,
        "origin_stop_name": row.origin_stop_name,
        "destination_stop_name": row.destination_stop_name,
        "departure_minutes": row.departure_minutes,
        "arrival_minutes": row.arrival_minutes,
        "duration_minutes": row.duration_minutes,
        "n_stops": row.n_stops,
        "distance_km": row.distance_km,
        "type_train": row.type_train,
        "kgCO2_emis": row.co2_estime / 1000,
    } for row in rows]
    return pd.DataFrame(data)


def _build_trips_query(
    db: Session,
    country: Optional[str],
    type_train: Optional[str],
    origin: Optional[str],
    destination: Optional[str],
    min_distance_km: Optional[float],
    max_distance_km: Optional[float],
):
    """Construit la requête SQLAlchemy filtrée sur Trip, sans charger les lignes."""
    query = db.query(Trip)

    if country:
        query = query.filter(Trip.country.ilike(country))
    if type_train:
        query = query.filter(Trip.type_train.ilike(type_train))
    if origin:
        query = query.filter(Trip.origin_stop_name.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Trip.destination_stop_name.ilike(f"%{destination}%"))
    if min_distance_km is not None:
        query = query.filter(Trip.distance_km >= min_distance_km)
    if max_distance_km is not None:
        query = query.filter(Trip.distance_km <= max_distance_km)

    return query


def _optional_float(value) -> Optional[float]:
    """Convertit une valeur potentiellement absente en float JSON-compatible."""
    if value is None:
        return None
    return float(value)


def _trip_to_trajet(row: Trip) -> TrajetOutput:
    """Convertit une ligne ORM Trip en contrat API stable."""
    return TrajetOutput(
        id=str(row.trip_id),
        route_id=str(row.route_id) if row.route_id is not None else "",
        route_long_name=row.route_long_name,
        origin_stop_name=row.origin_stop_name,
        destination_stop_name=row.destination_stop_name,
        country=row.country,
        type_train=row.type_train,
        distance_km=float(row.distance_km),
        duration_minutes=float(row.duration_minutes),
        n_stops=int(row.n_stops),
        departure_minutes=_optional_float(row.departure_minutes),
        arrival_minutes=_optional_float(row.arrival_minutes),
        kg_co2_emis=_optional_float(row.co2_estime / 1000 if row.co2_estime is not None else None),
    )


def _utc_now_iso() -> str:
    """Retourne un timestamp UTC ISO 8601 utilisable dans les réponses API."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _round_metric(value: float) -> float:
    """Arrondit les agrégats numériques pour des réponses stables et lisibles."""
    return round(float(value), 3)


def _volume_buckets(trips: pd.DataFrame, group_column: str) -> list[VolumeBucket]:
    """Construit des agrégats de volume pour une colonne du dataset."""
    grouped = (
        trips.groupby(group_column, dropna=False)
        .agg(
            total_trajets=("trip_id", "count"),
            total_distance_km=("distance_km", "sum"),
            total_kg_co2_emis=("kgCO2_emis", "sum"),
        )
        .reset_index()
        .sort_values(["total_trajets", group_column], ascending=[False, True])
    )

    return [
        VolumeBucket(
            key="unknown" if pd.isna(row[group_column]) else str(row[group_column]),
            total_trajets=int(row["total_trajets"]),
            total_distance_km=_round_metric(row["total_distance_km"]),
            total_kg_co2_emis=_round_metric(row["total_kg_co2_emis"]),
        )
        for _, row in grouped.iterrows()
    ]


def _model_health(name: str, available: bool, error: Optional[str] = None) -> dict:
    """Normalise l'état d'un modèle pour /health."""
    payload = {"status": "ok" if available else "unavailable"}
    if error:
        payload["error"] = error
    return {name: payload}


def _dataset_health(db: Session) -> dict:
    """Retourne l'état de la base de données sans masquer les erreurs de lecture."""
    try:
        count = db.query(Trip).count()
        return {"status": "ok", "rows": count, "columns": 13}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", tags=["Général"])
def root():
    """Message d'accueil — liste les routes disponibles."""
    return {
        "message": "ObRail Europe — API de prédiction ferroviaire",
        "version": "2.0.0",
        "routes": {
            "GET  /health":               "Statut de l'API, du dataset et des modèles",
            "GET  /trajets":              "Liste paginée et filtrable des trajets",
            "GET  /trajets/{id}":         "Détail d'un trajet par trip_id",
            "GET  /stats/volumes":        "Volumes agrégés par pays et type de train",
            "GET  /metrics":              "Métriques Prometheus de l'API",
            "POST /predict/substitution": "Classification substitution avion/train",
            "POST /predict/co2":          "Estimation CO2 futur selon scénario",
            "GET  /docs":                 "Documentation interactive (Swagger)",
        },
    }


@app.get("/trajets", response_model=TrajetsResponse, tags=["Données"])
def list_trajets(
    page: int = Query(1, ge=1, description="Page à retourner, indexée à partir de 1"),
    page_size: int = Query(25, ge=1, le=100, description="Nombre de trajets par page"),
    country: Optional[str] = Query(None, min_length=2, max_length=2, description="Filtre par code pays, ex. FR"),
    type_train: Optional[str] = Query(None, description="Filtre par type de train, ex. electric ou diesel"),
    origin: Optional[str] = Query(None, description="Recherche partielle sur la gare de départ"),
    destination: Optional[str] = Query(None, description="Recherche partielle sur la gare d'arrivée"),
    min_distance_km: Optional[float] = Query(None, ge=0, description="Distance minimale en kilomètres"),
    max_distance_km: Optional[float] = Query(None, ge=0, description="Distance maximale en kilomètres"),
    db: Session = Depends(get_db),
):
    """Retourne les trajets harmonisés avec pagination et filtres simples."""
    if (
        min_distance_km is not None
        and max_distance_km is not None
        and min_distance_km > max_distance_km
    ):
        raise HTTPException(
            status_code=422,
            detail="min_distance_km doit être inférieur ou égal à max_distance_km",
        )

    query = _build_trips_query(
        db=db,
        country=country,
        type_train=type_train,
        origin=origin,
        destination=destination,
        min_distance_km=min_distance_km,
        max_distance_km=max_distance_km,
    )

    total = query.count()
    total_pages = ceil(total / page_size) if total else 0
    rows = (
        query.order_by(Trip.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    items = [_trip_to_trajet(row) for row in rows]

    return TrajetsResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=items,
    )


@app.get("/trajets/{trajet_id}", response_model=TrajetOutput, tags=["Données"])
def get_trajet(trajet_id: str, db: Session = Depends(get_db)):
    """Retourne le détail d'un trajet à partir de son identifiant stable trip_id."""
    row = db.query(Trip).filter(Trip.trip_id == trajet_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Trajet '{trajet_id}' introuvable")

    return _trip_to_trajet(row)


@app.get("/stats/volumes", response_model=StatsVolumesResponse, tags=["Données"])
def stats_volumes(db: Session = Depends(get_db)):
    """Expose des volumes globaux et agrégés pour le tableau de bord ObRail."""
    try:
        trips = _load_trips_from_db(db)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    return StatsVolumesResponse(
        generated_at=_utc_now_iso(),
        total_trajets=int(len(trips)),
        total_countries=int(trips["country"].nunique(dropna=True)),
        total_routes=int(trips["route_id"].nunique(dropna=True)),
        total_distance_km=_round_metric(trips["distance_km"].sum()),
        total_kg_co2_emis=_round_metric(trips["kgCO2_emis"].sum()),
        by_country=_volume_buckets(trips, "country"),
        by_type_train=_volume_buckets(trips, "type_train"),
    )


@app.get("/health", tags=["Général"])
def health(db: Session = Depends(get_db)):
    """Vérifie que l'API, le dataset et les deux modèles sont opérationnels."""
    dataset = _dataset_health(db)
    models = {}
    models.update(
        _model_health(
            "classification_substitution",
            _substitution_ok,
            None if _substitution_ok else _substitution_error,
        )
    )
    models.update(
        _model_health(
            "regression_co2",
            _co2_ok,
            None if _co2_ok else _co2_error,
        )
    )

    dependency_statuses = [dataset["status"], *(model["status"] for model in models.values())]
    if all(status == "ok" for status in dependency_statuses):
        status = "ok"
    elif dataset["status"] != "ok":
        status = "unavailable"
    else:
        status = "degraded"

    return {
        "status": status,
        "timestamp": _utc_now_iso(),
        "dataset": dataset,
        "models": models,
    }


@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
def metrics():
    """Expose les métriques Prometheus collectées par le backend."""
    lines = [
        "# HELP obrail_api_info Static API information.",
        "# TYPE obrail_api_info gauge",
        'obrail_api_info{app="obrail-backend",version="2.0.0"} 1',
        *_dependency_metrics_lines(),
        *_http_metrics_lines(),
    ]
    return PlainTextResponse("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


@app.post("/predict", response_model=SubstitutionOutput, tags=["Classification"])
def predict_compat(liaison: LiaisonSubstitutionInput):
    """
    [Compatibilité v1] Prédit si une liaison est candidate à la substitution avion/train.
    Identique à POST /predict/substitution — conservée pour ne pas casser les intégrations existantes.
    """
    return _predict_substitution_logic(liaison)


@app.post("/predict/substitution", response_model=SubstitutionOutput, tags=["Classification"])
def predict_substitution(liaison: LiaisonSubstitutionInput):
    """
    Prédit si une liaison ferroviaire est candidate à remplacer un vol aérien.

    - **1** : liaison substituable (distance 300-1500 km, durée < 8h)
    - **0** : liaison non substituable
    """
    return _predict_substitution_logic(liaison)


def _predict_substitution_logic(liaison: LiaisonSubstitutionInput) -> SubstitutionOutput:
    """Logique commune aux routes /predict et /predict/substitution."""
    if not _substitution_ok:
        raise HTTPException(status_code=503, detail=f"Modèle de classification indisponible : {_substitution_error}")
    try:
        X = _build_substitution_df(liaison)
        X_scaled = pd.DataFrame(_scaler.transform(X), columns=X.columns)
        prediction = int(_model_substitution.predict(X_scaled)[0])
        proba = float(_model_substitution.predict_proba(X_scaled)[0][1])
        label = "Substituable à l'avion" if prediction == 1 else "Non substituable"
        return SubstitutionOutput(
            substitution_avion=prediction,
            probabilite=round(proba, 4),
            label=label,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Valeur invalide : {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction : {e}")


@app.post("/predict/co2", response_model=CO2Output, tags=["Régression CO2"])
def predict_co2(liaison: LiaisonCO2Input):
    """
    Estime les émissions CO2 futures d'une liaison ferroviaire selon un scénario.

    Scénarios disponibles :
    - **reference** : pas de changement — baseline actuel
    - **diesel_50_electrique** : trains diesel à -50% d'émissions
    - **conso_moins_15** : consommation réduite de 15% sur tous les trains
    - **distance_moins_10** : trajets raccourcis de 10%

    Retourne le CO2 estimé en **kgCO2**.
    """
    if not _co2_ok:
        raise HTTPException(status_code=503, detail=f"Modèle de régression CO2 indisponible : {_co2_error}")

    scenarios_valides = {"reference", "diesel_50_electrique", "conso_moins_15", "distance_moins_10"}
    if liaison.scenario not in scenarios_valides:
        raise HTTPException(
            status_code=422,
            detail=f"Scénario '{liaison.scenario}' inconnu. Valeurs acceptées : {sorted(scenarios_valides)}"
        )

    try:
        X = _build_co2_df(liaison)
        co2_predit = float(_model_co2.predict(X)[0])
        return CO2Output(
            scenario=liaison.scenario,
            co2_estime_kg=round(co2_predit, 4),
            label=f"CO2 estimé : {co2_predit:.2f} kgCO2 (scénario : {liaison.scenario})",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de prédiction CO2 : {e}")

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_root_documents_operational_routes():
    response = client.get("/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "2.0.0"
    assert payload["routes"]["GET  /trajets"] == "Liste paginée et filtrable des trajets"
    assert payload["routes"]["GET  /metrics"] == "Métriques Prometheus de l'API"

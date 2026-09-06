import pytest
from fastapi.testclient import TestClient

from app.db.database import Base, engine
from app.main import app


@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_scan_requires_authorization_confirmation(client):
    response = client.post(
        "/api/scans",
        json={"target_url": "http://localhost:3000", "authorization_confirmed": False},
    )
    assert response.status_code == 400
    assert "authorization" in response.json()["detail"].lower()


def test_scan_rejects_non_http_target(client):
    response = client.post(
        "/api/scans",
        json={"target_url": "localhost:3000", "authorization_confirmed": True},
    )
    assert response.status_code == 422


def test_unknown_scan_returns_404(client):
    assert client.get("/api/scans/999999").status_code == 404
    assert client.get("/api/scans/999999/findings").status_code == 404

import pytest

pytestmark = pytest.mark.integration


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_db(client):
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_db_unavailable(client, monkeypatch):
    monkeypatch.setenv("DB_PORT", "1")  # nadie escucha aquí
    response = client.get("/health/db")
    assert response.status_code == 503

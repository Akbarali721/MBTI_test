"""/health — monitoring shu javobga qarab xizmatni tirik deb hisoblaydi."""

from sqlalchemy.exc import OperationalError

from app import main


def test_health_reports_ok_when_the_database_answers(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_503_when_the_database_is_down(client, monkeypatch):
    class _BrokenEngine:
        def connect(self):
            raise OperationalError("SELECT 1", {}, Exception("baza yopiq"))

    monkeypatch.setattr(main, "engine", _BrokenEngine())

    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "error"}


def test_health_is_hidden_from_the_openapi_schema(client):
    schema = client.get("/openapi.json").json()
    assert "/health" not in schema["paths"]

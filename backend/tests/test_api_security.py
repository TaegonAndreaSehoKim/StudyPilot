from pathlib import Path

from fastapi.testclient import TestClient


def make_client(tmp_path: Path, monkeypatch, *, token: str | None = None, environment: str = "development") -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'security.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("USE_FAKE_AI", "true")
    monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if token:
        monkeypatch.setenv("BACKEND_ACCESS_TOKEN", token)
    else:
        monkeypatch.delenv("BACKEND_ACCESS_TOKEN", raising=False)

    from app.config import get_settings
    from app.database import configure_database, create_db_and_tables
    from app.main import create_app

    get_settings.cache_clear()
    configure_database(database_url)
    create_db_and_tables()
    return TestClient(create_app())


def test_mutations_are_open_in_local_development_without_token(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch)

    response = client.post("/courses", json={"title": "OMSCS AI"})

    assert response.status_code == 201


def test_health_is_public_when_token_is_configured(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch, token="secret")

    response = client.get("/health")

    assert response.status_code == 200


def test_mutations_require_access_token_when_configured(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch, token="secret")

    missing = client.post("/courses", json={"title": "OMSCS AI"})
    wrong = client.post("/courses", json={"title": "OMSCS AI"}, headers={"X-StudyPilot-Key": "wrong"})
    correct = client.post("/courses", json={"title": "OMSCS AI"}, headers={"X-StudyPilot-Key": "secret"})

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert correct.status_code == 201


def test_production_requires_configured_access_token(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch, environment="production")

    response = client.post("/courses", json={"title": "OMSCS AI"})

    assert response.status_code == 500
    assert "BACKEND_ACCESS_TOKEN" in response.json()["detail"]

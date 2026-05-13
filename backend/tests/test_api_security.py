from pathlib import Path

from fastapi.testclient import TestClient


def make_client(
    tmp_path: Path,
    monkeypatch,
    *,
    token: str | None = None,
    environment: str = "development",
    mutation_limit: int | None = None,
    ai_limit: int | None = None,
) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'security.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    monkeypatch.setenv("USE_FAKE_AI", "true")
    monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if mutation_limit is not None:
        monkeypatch.setenv("MUTATION_RATE_LIMIT_PER_MINUTE", str(mutation_limit))
    else:
        monkeypatch.delenv("MUTATION_RATE_LIMIT_PER_MINUTE", raising=False)
    if ai_limit is not None:
        monkeypatch.setenv("AI_RATE_LIMIT_PER_MINUTE", str(ai_limit))
    else:
        monkeypatch.delenv("AI_RATE_LIMIT_PER_MINUTE", raising=False)
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


def test_mutating_requests_are_rate_limited(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch, mutation_limit=2)

    first = client.post("/courses", json={"title": "OMSCS AI"})
    second = client.post("/courses", json={"title": "OMSCS ML"})
    third = client.post("/courses", json={"title": "OMSCS DB"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert third.status_code == 429
    assert "Too many write requests" in third.json()["detail"]


def test_ai_generation_requests_have_stricter_rate_limit(tmp_path: Path, monkeypatch) -> None:
    client = make_client(tmp_path, monkeypatch, mutation_limit=20, ai_limit=1)
    course_response = client.post("/courses", json={"title": "OMSCS AI"})
    course_id = course_response.json()["id"]
    text = (
        "Artificial Intelligence studies rational agents. Search algorithms explore state spaces. "
        "Heuristics guide search toward promising solutions. Planning uses actions and goals."
    )
    upload_response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.md", text.encode("utf-8"), "text/markdown")},
    )
    document_id = upload_response.json()["id"]

    first = client.post(f"/documents/{document_id}/summaries", json={"summary_type": "concise"})
    second = client.post(f"/documents/{document_id}/flashcards", json={"count": 2})

    assert first.status_code == 201
    assert second.status_code == 429
    assert "Too many AI generation requests" in second.json()["detail"]

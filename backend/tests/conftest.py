import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def storage_dir(tmp_path: Path) -> Path:
    return tmp_path / "storage"


@pytest.fixture()
def client(tmp_path: Path, storage_dir: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    database_url = f"sqlite:///{tmp_path / 'test.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("USE_FAKE_AI", "true")
    monkeypatch.setenv("OCR_PROVIDER", "fake")
    monkeypatch.delenv("BACKEND_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from app.config import get_settings
    from app.database import configure_database, create_db_and_tables, drop_db_and_tables
    from app.main import create_app

    get_settings.cache_clear()
    configure_database(database_url)
    create_db_and_tables()

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    drop_db_and_tables()
    get_settings.cache_clear()


@pytest.fixture()
def course_id(client: TestClient) -> int:
    response = client.post("/courses", json={"title": "OMSCS AI", "description": "AI notes"})
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture()
def document_id(client: TestClient, course_id: int) -> int:
    text = (
        "Artificial Intelligence studies rational agents. Search algorithms explore state spaces. "
        "Heuristics guide search toward promising solutions. Adversarial search models competitive games."
    )
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.md", text.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "extracted"
    return response.json()["id"]

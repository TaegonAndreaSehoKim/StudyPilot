from fastapi.testclient import TestClient


def test_upload_txt_document(client: TestClient, course_id: int) -> None:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.txt", b"Search uses states, actions, and transition models.", "text/plain")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["file_type"] == ".txt"
    assert body["char_count"] > 0
    assert body["status"] == "extracted"

    detail = client.get(f"/documents/{body['id']}")
    assert detail.status_code == 200
    assert "Search uses states" in detail.json()["preview"]


def test_upload_md_document(client: TestClient, course_id: int) -> None:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.md", b"# A*\n\nA* combines path cost and heuristic estimates.", "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json()["file_type"] == ".md"


def test_reject_unsupported_extension(client: TestClient, course_id: int) -> None:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.docx", b"not supported", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_reject_oversized_file(client: TestClient, course_id: int, monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    get_settings.cache_clear()

    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.txt", b"x", "text/plain")},
    )

    assert response.status_code == 413

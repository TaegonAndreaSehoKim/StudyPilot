from pathlib import Path

from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


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

    text_response = client.get(f"/documents/{body['id']}/text")
    assert text_response.status_code == 200
    assert text_response.json()["text"] == "Search uses states, actions, and transition models."

    download_response = client.get(f"/documents/{body['id']}/download")
    assert download_response.status_code == 200
    assert download_response.content == b"Search uses states, actions, and transition models."


def test_upload_md_document(client: TestClient, course_id: int) -> None:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.md", b"# A*\n\nA* combines path cost and heuristic estimates.", "text/markdown")},
    )

    assert response.status_code == 201
    assert response.json()["file_type"] == ".md"


def test_upload_text_based_pdf_document(client: TestClient, course_id: int) -> None:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.pdf", (FIXTURES_DIR / "text_notes.pdf").read_bytes(), "application/pdf")},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["file_type"] == ".pdf"
    assert body["status"] == "extracted"
    assert body["char_count"] > 100

    detail = client.get(f"/documents/{body['id']}")
    assert detail.status_code == 200
    assert "Artificial Intelligence studies rational agents" in detail.json()["preview"]


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


def test_delete_document_removes_uploaded_file(client: TestClient, course_id: int, storage_dir: Path) -> None:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.txt", b"Search uses states and actions.", "text/plain")},
    )
    assert response.status_code == 201
    document_id = response.json()["id"]
    documents_dir = storage_dir / "documents"
    assert len(list(documents_dir.iterdir())) == 1

    delete_response = client.delete(f"/documents/{document_id}")

    assert delete_response.status_code == 204
    assert list(documents_dir.iterdir()) == []

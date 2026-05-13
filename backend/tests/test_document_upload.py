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
    assert body["page_count"] == 1
    assert body["extracted_page_count"] == 1
    assert body["extraction_method"] == "text"
    assert body["ocr_status"] == "not_required"

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
    assert body["page_count"] >= 1
    assert body["extracted_page_count"] >= 1
    assert body["extraction_method"] == "pypdf"

    detail = client.get(f"/documents/{body['id']}")
    assert detail.status_code == 200
    assert "Artificial Intelligence studies rational agents" in detail.json()["preview"]


def test_scanned_pdf_can_be_marked_for_ocr_and_processed(client: TestClient, course_id: int, monkeypatch) -> None:
    from app.services import document_extractor

    class EmptyPdfReader:
        pages = [object(), object()]

    monkeypatch.setattr(document_extractor, "PdfReader", lambda _: EmptyPdfReader())
    monkeypatch.setattr(document_extractor, "_extract_pdf_page_text", lambda _: "")

    upload_response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("scan.pdf", b"%PDF scanned placeholder", "application/pdf")},
    )

    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["status"] == "needs_ocr"
    assert uploaded["ocr_status"] == "available"
    assert uploaded["page_count"] == 2
    assert uploaded["extracted_page_count"] == 0

    summary_response = client.post(f"/documents/{uploaded['id']}/summaries", json={"summary_type": "concise"})
    assert summary_response.status_code == 400

    ocr_response = client.post(f"/documents/{uploaded['id']}/ocr")
    assert ocr_response.status_code == 202
    ocr_job = ocr_response.json()
    assert ocr_job["document_id"] == uploaded["id"]
    assert ocr_job["provider"] == "fake"

    job_response = client.get(f"/ocr-jobs/{ocr_job['id']}")
    assert job_response.status_code == 200
    assert job_response.json()["status"] == "completed"

    document_response = client.get(f"/documents/{uploaded['id']}/text")
    assert document_response.status_code == 200
    ocr_body = document_response.json()
    assert ocr_body["status"] == "extracted"
    assert ocr_body["ocr_status"] == "completed"
    assert ocr_body["extraction_method"] == "fake_ocr"
    assert ocr_body["extracted_page_count"] == 2
    assert "Fake OCR extracted study text" in ocr_body["text"]

    summary_after_ocr = client.post(f"/documents/{uploaded['id']}/summaries", json={"summary_type": "concise"})
    assert summary_after_ocr.status_code == 201


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

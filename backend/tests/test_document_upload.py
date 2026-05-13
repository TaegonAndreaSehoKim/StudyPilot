from pathlib import Path

from fastapi.testclient import TestClient


def _simple_pdf_bytes(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{index} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"
    xref_offset = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        pdf += f"{offset:010d} 00000 n \n".encode("ascii")
    pdf += (
        b"trailer\n"
        + f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii")
        + b"startxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    return pdf


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


def test_upload_text_based_pdf_document(client: TestClient, course_id: int) -> None:
    text = (
        "Artificial Intelligence studies rational agents. Search algorithms use heuristics "
        "to explore state spaces. Planning systems use actions preconditions effects and goals."
    )

    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.pdf", _simple_pdf_bytes(text), "application/pdf")},
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

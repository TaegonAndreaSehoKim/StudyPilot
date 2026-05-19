from pathlib import Path

from fastapi.testclient import TestClient


def test_course_crud(client: TestClient) -> None:
    create_response = client.post("/courses", json={"title": "OMSCS AI", "description": "AI notes"})
    assert create_response.status_code == 201
    course = create_response.json()

    list_response = client.get("/courses")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/courses/{course['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["document_count"] == 0

    update_response = client.patch(f"/courses/{course['id']}", json={"title": "OMSCS ML"})
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "OMSCS ML"

    delete_response = client.delete(f"/courses/{course['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/courses/{course['id']}")
    assert missing_response.status_code == 404


def test_delete_course_removes_uploaded_files(client: TestClient, storage_dir: Path) -> None:
    course_response = client.post("/courses", json={"title": "OMSCS AI", "description": "AI notes"})
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]
    upload_response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id)},
        files={"file": ("notes.md", b"# Search\n\nSearch explores state spaces.", "text/markdown")},
    )
    assert upload_response.status_code == 201
    documents_dir = storage_dir / "documents"
    assert len(list(documents_dir.iterdir())) == 1

    delete_response = client.delete(f"/courses/{course_id}")

    assert delete_response.status_code == 204
    assert list(documents_dir.iterdir()) == []


def test_delete_course_with_section_outputs_schedule_and_attempts(client: TestClient, storage_dir: Path) -> None:
    course_response = client.post("/courses", json={"title": "OMSCS AI", "description": "AI notes"})
    assert course_response.status_code == 201
    course_id = course_response.json()["id"]

    section_response = client.post(f"/courses/{course_id}/sections", json={"title": "Midterm 1"})
    assert section_response.status_code == 201
    section_id = section_response.json()["id"]

    upload_response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id), "section_id": str(section_id)},
        files={"file": ("notes.md", b"# Search\n\nSearch explores state spaces with heuristics.", "text/markdown")},
    )
    assert upload_response.status_code == 201
    document_id = upload_response.json()["id"]

    assert client.post(f"/sections/{section_id}/summaries", json={"summary_type": "concise"}).status_code == 201
    assert client.post(f"/sections/{section_id}/explanations", json={}).status_code == 201
    quiz_response = client.post(f"/sections/{section_id}/quizzes", json={"question_count": 2, "difficulty": "mixed"})
    assert quiz_response.status_code == 201
    quiz = quiz_response.json()
    assert client.post(
        f"/quizzes/{quiz['id']}/attempts",
        json={"answers": [{"question_id": question["id"], "selected_answer": "Z"} for question in quiz["questions"]]},
    ).status_code == 201
    assert client.post(
        f"/courses/{course_id}/schedule",
        json={"title": "Exam", "event_type": "exam", "due_at": "2026-05-31T23:59:00Z", "reminder_minutes_before": 60},
    ).status_code == 201

    delete_response = client.delete(f"/courses/{course_id}")

    assert delete_response.status_code == 204
    assert client.get(f"/courses/{course_id}").status_code == 404
    assert client.get(f"/sections/{section_id}").status_code == 404
    assert client.get(f"/documents/{document_id}").status_code == 404
    assert list((storage_dir / "documents").iterdir()) == []

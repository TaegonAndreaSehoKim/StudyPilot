from fastapi.testclient import TestClient


def test_dashboard_counts(client: TestClient, course_id: int, document_id: int) -> None:
    client.post(f"/documents/{document_id}/summaries", json={"summary_type": "exam"})
    client.post(f"/documents/{document_id}/flashcards", json={"count": 2})
    client.post(f"/documents/{document_id}/quizzes", json={"question_count": 2, "difficulty": "easy"})

    response = client.get("/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["course_count"] == 1
    assert body["document_count"] == 1
    assert body["summary_count"] == 1
    assert body["flashcard_count"] == 2
    assert body["quiz_count"] == 1

    course_dashboard = client.get(f"/courses/{course_id}/dashboard")
    assert course_dashboard.status_code == 200
    assert course_dashboard.json()["quiz_count"] == 1

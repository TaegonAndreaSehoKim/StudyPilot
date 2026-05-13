from fastapi.testclient import TestClient


def test_generate_concise_summary(client: TestClient, document_id: int) -> None:
    response = client.post(f"/documents/{document_id}/summaries", json={"summary_type": "concise"})

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"] == document_id
    assert body["key_points"]

    list_response = client.get(f"/documents/{document_id}/summaries")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    detail_response = client.get(f"/summaries/{body['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == body["id"]


def test_list_course_summaries(client: TestClient, course_id: int, document_id: int) -> None:
    first = client.post(f"/documents/{document_id}/summaries", json={"summary_type": "concise"})
    second = client.post(f"/documents/{document_id}/summaries", json={"summary_type": "exam"})
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(f"/courses/{course_id}/summaries")

    assert response.status_code == 200
    body = response.json()
    assert [summary["id"] for summary in body] == [second.json()["id"], first.json()["id"]]


def test_get_missing_summary_returns_404(client: TestClient) -> None:
    response = client.get("/summaries/999999")

    assert response.status_code == 404

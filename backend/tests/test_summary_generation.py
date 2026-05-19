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


def test_generate_additional_explanation(client: TestClient, document_id: int) -> None:
    response = client.post(
        f"/documents/{document_id}/explanations",
        json={"focus": "Explain why update loops matter for movement."},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["document_id"] == document_id
    assert body["summary_type"] == "explanation"
    assert body["key_points"]
    assert body["key_terms"]


def test_explanation_uses_dedicated_endpoint(client: TestClient, document_id: int) -> None:
    response = client.post(f"/documents/{document_id}/summaries", json={"summary_type": "explanation"})

    assert response.status_code == 422


def test_get_missing_summary_returns_404(client: TestClient) -> None:
    response = client.get("/summaries/999999")

    assert response.status_code == 404


def test_delete_summary(client: TestClient, document_id: int) -> None:
    create_response = client.post(f"/documents/{document_id}/summaries", json={"summary_type": "concise"})
    assert create_response.status_code == 201
    summary_id = create_response.json()["id"]

    delete_response = client.delete(f"/summaries/{summary_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/summaries/{summary_id}")
    assert get_response.status_code == 404

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

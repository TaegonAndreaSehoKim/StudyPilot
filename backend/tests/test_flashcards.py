from fastapi.testclient import TestClient


def test_generate_flashcards(client: TestClient, document_id: int) -> None:
    response = client.post(f"/documents/{document_id}/flashcards", json={"count": 4})

    assert response.status_code == 201
    body = response.json()
    assert len(body) == 4
    assert body[0]["front"]

    list_response = client.get(f"/documents/{document_id}/flashcards")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 4

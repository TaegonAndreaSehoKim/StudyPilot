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


def test_list_course_flashcards(client: TestClient, course_id: int, document_id: int) -> None:
    first = client.post(f"/documents/{document_id}/flashcards", json={"count": 2})
    second = client.post(f"/documents/{document_id}/flashcards", json={"count": 1})
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(f"/courses/{course_id}/flashcards")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_list_course_flashcards_missing_course(client: TestClient) -> None:
    response = client.get("/courses/999999/flashcards")

    assert response.status_code == 404

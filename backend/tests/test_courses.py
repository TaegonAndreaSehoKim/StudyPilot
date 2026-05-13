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

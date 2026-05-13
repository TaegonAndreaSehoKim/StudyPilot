from fastapi.testclient import TestClient


def test_generate_quiz_submit_attempt_and_update_weak_topic(client: TestClient, course_id: int, document_id: int) -> None:
    quiz_response = client.post(f"/documents/{document_id}/quizzes", json={"question_count": 3, "difficulty": "mixed"})
    assert quiz_response.status_code == 201
    quiz = quiz_response.json()
    assert len(quiz["questions"]) == 3

    answers = [
        {"question_id": question["id"], "selected_answer": "Z"}
        for question in quiz["questions"]
    ]
    attempt_response = client.post(f"/quizzes/{quiz['id']}/attempts", json={"answers": answers})
    assert attempt_response.status_code == 201
    attempt = attempt_response.json()
    assert attempt["score"] == 0
    assert attempt["total_questions"] == 3
    assert attempt["missed_topics"]

    weak_topics_response = client.get(f"/courses/{course_id}/weak-topics")
    assert weak_topics_response.status_code == 200
    assert weak_topics_response.json()[0]["miss_count"] >= 1


def test_list_course_quizzes(client: TestClient, course_id: int, document_id: int) -> None:
    first = client.post(f"/documents/{document_id}/quizzes", json={"question_count": 2, "difficulty": "mixed"})
    second = client.post(f"/documents/{document_id}/quizzes", json={"question_count": 1, "difficulty": "easy"})
    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get(f"/courses/{course_id}/quizzes")

    assert response.status_code == 200
    body = response.json()
    assert [quiz["id"] for quiz in body] == [second.json()["id"], first.json()["id"]]


def test_list_course_quizzes_missing_course(client: TestClient) -> None:
    response = client.get("/courses/999999/quizzes")

    assert response.status_code == 404

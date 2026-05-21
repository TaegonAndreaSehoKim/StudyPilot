from fastapi.testclient import TestClient


def _upload_section_document(client: TestClient, course_id: int, section_id: int, filename: str, text: str) -> dict:
    response = client.post(
        "/documents/upload",
        data={"course_id": str(course_id), "section_id": str(section_id)},
        files={"file": (filename, text.encode("utf-8"), "text/markdown")},
    )
    assert response.status_code == 201
    return response.json()


def test_section_workflow_generates_outputs_from_multiple_documents(client: TestClient, course_id: int) -> None:
    create_response = client.post(
        f"/courses/{course_id}/sections",
        json={"title": "Midterm 1", "description": "Search and planning exam scope"},
    )
    assert create_response.status_code == 201
    section = create_response.json()
    assert section["document_count"] == 0

    first_document = _upload_section_document(
        client,
        course_id,
        section["id"],
        "search.md",
        "Search algorithms explore state spaces. Heuristics guide search toward goals.",
    )
    second_document = _upload_section_document(
        client,
        course_id,
        section["id"],
        "planning.md",
        "Planning uses actions, preconditions, effects, and goals to create a plan.",
    )
    assert first_document["section_id"] == section["id"]
    assert second_document["section_id"] == section["id"]

    documents_response = client.get(f"/sections/{section['id']}/documents")
    assert documents_response.status_code == 200
    assert {document["id"] for document in documents_response.json()} == {first_document["id"], second_document["id"]}

    summary_response = client.post(f"/sections/{section['id']}/summaries", json={"summary_type": "exam"})
    assert summary_response.status_code == 201
    summary = summary_response.json()
    assert summary["section_id"] == section["id"]
    assert summary["document_id"] == first_document["id"]
    assert summary["title"] == "Midterm 1 - Exam Review Notes"
    assert summary["key_points"]

    quiz_response = client.post(f"/sections/{section['id']}/quizzes", json={"question_count": 3, "difficulty": "mixed"})
    assert quiz_response.status_code == 201
    quiz = quiz_response.json()
    assert quiz["section_id"] == section["id"]
    assert quiz["document_id"] == first_document["id"]
    assert len(quiz["questions"]) == 3

    dashboard_response = client.get(f"/courses/{course_id}/dashboard")
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert dashboard["section_count"] == 1
    assert dashboard["recent_sections"][0]["id"] == section["id"]
    assert dashboard["summary_count"] == 1
    assert dashboard["quiz_count"] == 1

    explanation_response = client.post(f"/sections/{section['id']}/explanations", json={"focus": "Help me understand planning."})
    assert explanation_response.status_code == 201
    explanation = explanation_response.json()
    assert explanation["section_id"] == section["id"]
    assert explanation["summary_type"] == "explanation"
    assert explanation["title"] == "Midterm 1 - Additional Explanation"
    assert explanation["key_points"]


def test_section_summaries_stay_scoped_with_duplicate_filenames(client: TestClient, course_id: int) -> None:
    movement_response = client.post(f"/courses/{course_id}/sections", json={"title": "02_Basic Agent Movement"})
    intro_response = client.post(f"/courses/{course_id}/sections", json={"title": "01_Introduction to Game AI"})
    assert movement_response.status_code == 201
    assert intro_response.status_code == 201
    movement = movement_response.json()
    intro = intro_response.json()

    movement_document = _upload_section_document(
        client,
        course_id,
        movement["id"],
        "transcript_en.txt",
        "Agent movement uses position, velocity, steering, and orientation updates.",
    )
    intro_document = _upload_section_document(
        client,
        course_id,
        intro["id"],
        "transcript_en.txt",
        "Game AI includes decision making, movement, planning, and behavior control.",
    )

    movement_summary_response = client.post(f"/sections/{movement['id']}/summaries", json={"summary_type": "detailed"})
    intro_summary_response = client.post(f"/sections/{intro['id']}/summaries", json={"summary_type": "detailed"})
    assert movement_summary_response.status_code == 201
    assert intro_summary_response.status_code == 201
    movement_summary = movement_summary_response.json()
    intro_summary = intro_summary_response.json()

    assert movement_summary["document_id"] == movement_document["id"]
    assert movement_summary["section_id"] == movement["id"]
    assert movement_summary["title"] == "02_Basic Agent Movement - Detailed Review Notes"
    assert intro_summary["document_id"] == intro_document["id"]
    assert intro_summary["section_id"] == intro["id"]
    assert intro_summary["title"] == "01_Introduction to Game AI - Detailed Review Notes"

    movement_list = client.get(f"/sections/{movement['id']}/summaries").json()
    intro_list = client.get(f"/sections/{intro['id']}/summaries").json()
    assert [summary["id"] for summary in movement_list] == [movement_summary["id"]]
    assert [summary["id"] for summary in intro_list] == [intro_summary["id"]]


def test_section_generation_requires_extracted_documents(client: TestClient, course_id: int) -> None:
    section_response = client.post(f"/courses/{course_id}/sections", json={"title": "Final Exam"})
    assert section_response.status_code == 201

    response = client.post(f"/sections/{section_response.json()['id']}/summaries", json={"summary_type": "concise"})

    assert response.status_code == 400


def test_section_update_and_delete_detaches_documents(client: TestClient, course_id: int) -> None:
    section_response = client.post(f"/courses/{course_id}/sections", json={"title": "Unit 1"})
    assert section_response.status_code == 201
    section_id = section_response.json()["id"]
    document = _upload_section_document(
        client,
        course_id,
        section_id,
        "unit.md",
        "Constraint satisfaction problems assign values while satisfying constraints.",
    )

    update_response = client.patch(
        f"/sections/{section_id}",
        json={"title": "Unit 1: CSP", "description": "Constraint satisfaction"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Unit 1: CSP"

    delete_response = client.delete(f"/sections/{section_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/sections/{section_id}").status_code == 404
    assert client.get(f"/documents/{document['id']}").json()["section_id"] is None

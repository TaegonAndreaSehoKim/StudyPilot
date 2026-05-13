from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def test_course_schedule_crud(client: TestClient, course_id: int) -> None:
    due_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    create_response = client.post(
        f"/courses/{course_id}/schedule",
        json={
            "title": "Project 1 due",
            "event_type": "assignment",
            "due_at": due_at,
            "notes": "Submit before midnight.",
        },
    )
    assert create_response.status_code == 201
    item = create_response.json()
    assert item["title"] == "Project 1 due"
    assert item["is_completed"] is False

    list_response = client.get(f"/courses/{course_id}/schedule")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    update_response = client.patch(f"/schedule/{item['id']}", json={"is_completed": True})
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["is_completed"] is True
    assert updated["completed_at"] is not None

    active_response = client.get(f"/courses/{course_id}/schedule", params={"include_completed": "false"})
    assert active_response.status_code == 200
    assert active_response.json() == []

    delete_response = client.delete(f"/schedule/{item['id']}")
    assert delete_response.status_code == 204
    missing_response = client.get(f"/schedule/{item['id']}")
    assert missing_response.status_code == 404


def test_course_schedule_orders_active_items_by_due_date(client: TestClient, course_id: int) -> None:
    later = (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()
    sooner = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    client.post(f"/courses/{course_id}/schedule", json={"title": "Later exam", "event_type": "exam", "due_at": later})
    client.post(f"/courses/{course_id}/schedule", json={"title": "Sooner reading", "event_type": "reading", "due_at": sooner})

    response = client.get(f"/courses/{course_id}/schedule")

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Sooner reading", "Later exam"]


def test_global_schedule_lists_all_courses_with_course_title(client: TestClient, course_id: int) -> None:
    second_course = client.post("/courses", json={"title": "Databases", "description": None}).json()
    later = (datetime.now(timezone.utc) + timedelta(days=4)).isoformat()
    sooner = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    completed = client.post(
        f"/courses/{course_id}/schedule",
        json={"title": "Completed milestone", "event_type": "project", "due_at": sooner},
    ).json()
    client.patch(f"/schedule/{completed['id']}", json={"is_completed": True})
    client.post(f"/courses/{course_id}/schedule", json={"title": "AI exam", "event_type": "exam", "due_at": later})
    client.post(
        f"/courses/{second_course['id']}/schedule",
        json={"title": "DB project", "event_type": "project", "due_at": sooner},
    )

    response = client.get("/schedule")

    assert response.status_code == 200
    body = response.json()
    assert [item["title"] for item in body] == ["DB project", "AI exam"]
    assert body[0]["course_title"] == "Databases"


def test_create_schedule_missing_course(client: TestClient) -> None:
    response = client.post(
        "/courses/999999/schedule",
        json={
            "title": "Missing",
            "event_type": "other",
            "due_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        },
    )

    assert response.status_code == 404

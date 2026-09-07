from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


def test_signup_registers_student_once():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert activities["Chess Club"]["participants"][-1] == (
        "new.student@mergington.edu"
    )


def test_signup_rejects_duplicate_email_case_insensitively():
    email = "new.student@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "  NEW.STUDENT@MERGINGTON.EDU "},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )
    assert activities["Chess Club"]["participants"].count(email) == 1


def test_signup_rejects_empty_email():
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is required"


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_full_activity():
    activity = activities["Chess Club"]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "last.student@mergington.edu"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Activity is full"
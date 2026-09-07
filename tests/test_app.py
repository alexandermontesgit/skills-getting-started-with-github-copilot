from src.app import activities


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_static_index_is_available(client):
    # Arrange
    static_index = "/static/index.html"

    # Act
    response = client.get(static_index)

    # Assert
    assert response.status_code == 200
    assert "Mergington High School" in response.text


def test_get_activities_returns_expected_data(client):
    # Arrange
    expected_activities = {
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Soccer Club",
        "Basketball Club",
        "Art Club",
        "Drama Club",
        "Debate Club",
        "Math Club",
    }

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    returned_activities = response.json()
    assert expected_activities.issubset(returned_activities)
    for activity in returned_activities.values():
        assert {"description", "schedule", "max_participants", "participants"} <= (
            activity.keys()
        )


def test_signup_normalizes_and_registers_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "  New.Student@Mergington.edu "

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new.student@mergington.edu for Chess Club"
    }
    assert "new.student@mergington.edu" in activities[activity_name]["participants"]


def test_signup_rejects_duplicate_without_mutating_participants(client):
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    client.post(f"/activities/{activity_name}/signup", params={"email": email})
    participants_after_first_signup = activities[activity_name]["participants"][:]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "  NEW.STUDENT@MERGINGTON.EDU "},
    )

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Student is already signed up for this activity"
    )
    assert activities[activity_name]["participants"] == participants_after_first_signup


def test_signup_rejects_empty_email_without_mutating_participants(client):
    # Arrange
    activity_name = "Chess Club"
    participants_before = activities[activity_name]["participants"][:]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "   "},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is required"
    assert activities[activity_name]["participants"] == participants_before


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_full_activity_without_mutating_participants(client):
    # Arrange
    activity_name = "Chess Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    participants_before = activity["participants"][:]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "last.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Activity is full"
    assert activity["participants"] == participants_before


def test_remove_participant_unregisters_student(client):
    # Arrange
    activity_name = "Chess Club"
    email = "  MICHAEL@MERGINGTON.EDU "

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in activities[activity_name]["participants"]


def test_remove_rejects_unknown_student_without_mutating_participants(client):
    # Arrange
    activity_name = "Chess Club"
    participants_before = activities[activity_name]["participants"][:]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "unknown@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Student is not signed up for this activity"
    )
    assert activities[activity_name]["participants"] == participants_before


def test_remove_rejects_empty_email_without_mutating_participants(client):
    # Arrange
    activity_name = "Chess Club"
    participants_before = activities[activity_name]["participants"][:]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "   "},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is required"
    assert activities[activity_name]["participants"] == participants_before


def test_remove_rejects_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_then_remove_completes_registration_cycle(client):
    # Arrange
    activity_name = "Art Club"
    email = "cycle.student@mergington.edu"

    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    remove_response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert signup_response.status_code == 200
    assert remove_response.status_code == 200
    assert email not in activities[activity_name]["participants"]

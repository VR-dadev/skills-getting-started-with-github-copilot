from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


def encode_activity(activity_name: str) -> str:
    return quote(activity_name, safe="")


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(deepcopy(original_activities))


def test_root_redirects_to_static_index():
    # Arrange
    url = "/"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activities_dictionary():
    # Arrange
    url = "/activities"

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert data["Chess Club"]["max_participants"] == 12
    assert "participants" in data["Chess Club"]


def test_signup_for_activity_succeeds():
    # Arrange
    activity_name = "Art Studio"
    encoded_name = encode_activity(activity_name)
    email = "newstudent@mergington.edu"
    url = f"/activities/{encoded_name}/signup"

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_unknown_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Club"
    encoded_name = encode_activity(activity_name)
    email = "student@mergington.edu"
    url = f"/activities/{encoded_name}/signup"

    # Act
    response = client.post(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_duplicate_signup_returns_400():
    # Arrange
    activity_name = "Programming Class"
    encoded_name = encode_activity(activity_name)
    email = "duplicate@mergington.edu"
    url = f"/activities/{encoded_name}/signup"

    # Act
    first_response = client.post(url, params={"email": email})
    second_response = client.post(url, params={"email": email})

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant_succeeds():
    # Arrange
    activity_name = "Art Studio"
    encoded_name = encode_activity(activity_name)
    email = "isabella@mergington.edu"
    url = f"/activities/{encoded_name}/signup"

    # Act
    response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    activity_name = "Chess Club"
    encoded_name = encode_activity(activity_name)
    email = "absent@mergington.edu"
    url = f"/activities/{encoded_name}/signup"

    # Act
    response = client.delete(url, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not signed up for this activity"

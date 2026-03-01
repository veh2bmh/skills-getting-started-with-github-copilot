"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

# Snapshot the original activity data so each test starts from a clean state
ORIGINAL_ACTIVITIES = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities dict before every test."""
    activities.clear()
    activities.update(copy.deepcopy(ORIGINAL_ACTIVITIES))
    yield


client = TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

def test_get_activities_returns_200():
    response = client.get("/activities")
    assert response.status_code == 200


def test_get_activities_contains_expected_keys():
    response = client.get("/activities")
    data = response.json()
    for name in ["Chess Club", "Programming Class", "Gym Class", "Soccer Team",
                 "Basketball Club", "Drama Club", "Art Workshop",
                 "Math Olympiad", "Science Club"]:
        assert name in data


def test_get_activities_structure():
    response = client.get("/activities")
    data = response.json()
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

def test_root_redirects_to_static():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (301, 302, 307, 308)
    assert response.headers["location"] == "/static/index.html"


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_signup_success():
    response = client.post(
        "/activities/Soccer%20Team/signup?email=new@mergington.edu"
    )
    assert response.status_code == 200
    assert "new@mergington.edu" in response.json()["message"]


def test_signup_adds_participant():
    client.post("/activities/Soccer%20Team/signup?email=new@mergington.edu")
    data = client.get("/activities").json()
    assert "new@mergington.edu" in data["Soccer Team"]["participants"]


def test_signup_activity_not_found():
    response = client.post(
        "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404


def test_signup_already_registered():
    client.post("/activities/Soccer%20Team/signup?email=dup@mergington.edu")
    response = client.post(
        "/activities/Soccer%20Team/signup?email=dup@mergington.edu"
    )
    assert response.status_code == 400


def test_signup_existing_participant_still_registered():
    """Participants pre-loaded in Chess Club should already be blocked."""
    response = client.post(
        "/activities/Chess%20Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

def test_unregister_success():
    response = client.delete(
        "/activities/Chess%20Club/signup?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    assert "michael@mergington.edu" in response.json()["message"]


def test_unregister_removes_participant():
    client.delete("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    data = client.get("/activities").json()
    assert "michael@mergington.edu" not in data["Chess Club"]["participants"]


def test_unregister_activity_not_found():
    response = client.delete(
        "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404


def test_unregister_not_registered():
    response = client.delete(
        "/activities/Chess%20Club/signup?email=nobody@mergington.edu"
    )
    assert response.status_code == 400

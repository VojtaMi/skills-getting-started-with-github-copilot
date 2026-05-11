import pytest
from fastapi.testclient import TestClient
from src.app import app, activities

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test to ensure isolation"""
    # Save original state
    original = {}
    for key, value in activities.items():
        original[key] = {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy()
        }

    yield

    # Restore original state
    activities.clear()
    activities.update(original)

def test_get_activities(client):
    """Test GET /activities returns all activities with correct structure"""
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # All activities present

    # Check structure of one activity
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess
    assert isinstance(chess["participants"], list)
    assert len(chess["participants"]) >= 0

def test_signup_success(client):
    """Test successful signup for an activity"""
    email = "test@example.com"
    activity = "Chess Club"

    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert f"Signed up {email} for {activity}" == data["message"]

    # Verify added to participants
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity]["participants"]

def test_signup_duplicate(client):
    """Test signup fails when student already signed up"""
    email = "duplicate@example.com"
    activity = "Programming Class"

    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")

    # Second signup should fail
    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]

def test_signup_invalid_activity(client):
    """Test signup fails for non-existent activity"""
    email = "test@example.com"
    activity = "NonExistent Activity"

    response = client.post(f"/activities/{activity}/signup?email={email}")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]

def test_unregister_success(client):
    """Test successful unregister from an activity"""
    email = "unregister@example.com"
    activity = "Gym Class"

    # First signup
    client.post(f"/activities/{activity}/signup?email={email}")

    # Then unregister
    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 200

    data = response.json()
    assert "message" in data
    assert f"Unregistered {email} from {activity}" == data["message"]

    # Verify removed from participants
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity]["participants"]

def test_unregister_not_signed_up(client):
    """Test unregister fails when student not signed up"""
    email = "notsigned@example.com"
    activity = "Soccer Team"

    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]

def test_unregister_invalid_activity(client):
    """Test unregister fails for non-existent activity"""
    email = "test@example.com"
    activity = "Invalid Activity"

    response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]

def test_root_redirect(client):
    """Test root endpoint redirects to static index"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Redirect status
    assert response.headers["location"] == "/static/index.html"
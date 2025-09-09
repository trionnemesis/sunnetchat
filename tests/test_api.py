import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set dummy environment variables for testing
os.environ["SLACK_SIGNING_SECRET"] = "test_secret"
os.environ["SLACK_BOT_TOKEN"] = "test_token"

from app.main import app, signature_verifier

client = TestClient(app)


@pytest.fixture
def mock_rag_core():
    """Fixture to mock the get_answer function."""
    with patch("app.main.get_answer") as mock_get_answer:
        mock_get_answer.return_value = "這是來自 RAG 核心的模擬答案。"
        yield mock_get_answer


@pytest.fixture
def mock_slack_client():
    """Fixture to mock the Slack WebClient."""
    with patch("app.main.slack_client") as mock_client:
        yield mock_client


# --- Test Cases ---


def test_health_check():
    """Tests the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Sunnetchat Bot is running."}


def test_slack_url_verification():
    """Tests the one-time URL verification challenge from Slack."""
    challenge_data = {"type": "url_verification", "challenge": "test_challenge_string"}
    # Mock signature verification to always pass for this test
    with patch.object(signature_verifier, "is_valid_request", return_value=True):
        response = client.post("/slack/events", json=challenge_data)
    assert response.status_code == 200
    assert response.json() == {"challenge": "test_challenge_string"}


def test_app_mention_event(mock_rag_core, mock_slack_client):
    """Tests a valid app_mention event, ensuring the RAG core and Slack client are called."""
    event_data = {
        "type": "event_callback",
        "event": {
            "type": "app_mention",
            "text": "<@U12345> 什麼是 TDD?",
            "user": "U_TEST",
            "channel": "C_TEST",
            "ts": "12345.67890",
        },
    }
    with patch.object(signature_verifier, "is_valid_request", return_value=True):
        response = client.post("/slack/events", json=event_data)

    # The immediate response should be 200 OK
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Since the core logic runs in the background, we can't directly assert its calls here.
    # This requires more advanced testing of background tasks, but for now, we ensure the API accepts the event.


def test_invalid_signature():
    """Tests that a request with an invalid signature is rejected."""
    with patch.object(signature_verifier, "is_valid_request", return_value=False):
        response = client.post("/slack/events", json={})
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid request signature"}

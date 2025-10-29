import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Set dummy environment variables for testing
os.environ["SLACK_SIGNING_SECRET"] = "test_secret"
os.environ["SLACK_BOT_TOKEN"] = "test_token"

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_slack_app():
    """Fixture to mock the Slack app."""
    with patch("app.main.slack_app") as mock_app:
        yield mock_app


@pytest.fixture
def mock_agent():
    """Fixture to mock the core agent."""
    with patch("app.main.get_agent") as mock_get_agent:
        mock_instance = MagicMock()
        mock_instance.process_question.return_value = {
            "generation": "這是來自代理的模擬答案。",
            "status": "completed",
        }
        mock_get_agent.return_value = mock_instance
        yield mock_get_agent


# --- Test Cases ---


def test_health_check():
    """Tests the root health check endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_slack_url_verification():
    """Tests the one-time URL verification challenge from Slack."""
    challenge_data = {"type": "url_verification", "challenge": "test_challenge_string"}
    # Mock the app handler to simulate URL verification
    with patch("app.main.app_handler") as mock_handler:
        from fastapi import Response

        mock_response = Response(
            content='{"challenge": "test_challenge_string"}',
            media_type="application/json",
        )
        mock_handler.handle.return_value = mock_response
        response = client.post("/slack/events", json=challenge_data)
    assert response.status_code == 200


def test_app_mention_event(mock_slack_app, mock_agent):
    """Tests a valid app_mention event, ensuring the handler processes it correctly."""
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
    # Mock the app handler response
    with patch("app.main.app_handler") as mock_handler:
        from fastapi import Response

        mock_response = Response(
            content='{"status": "ok"}', media_type="application/json"
        )
        mock_handler.handle.return_value = mock_response
        response = client.post("/slack/events", json=event_data)

    # The immediate response should be 200 OK
    assert response.status_code == 200


def test_slack_endpoint_with_mock_handler():
    """Tests that the Slack endpoint uses the handler correctly."""
    with patch("app.main.app_handler") as mock_handler:
        from fastapi import Response

        mock_response = Response(
            content='{"test": "response"}', media_type="application/json"
        )
        mock_handler.handle.return_value = mock_response
        response = client.post("/slack/events", json={})
    assert response.status_code == 200

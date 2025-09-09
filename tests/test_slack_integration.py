from unittest.mock import patch
from fastapi.testclient import TestClient


# We patch the App class inside the factory module. This is the key.
@patch("app.factory.App")
@patch("app.factory.rag_chain")
def test_slack_mention_with_factory(mock_rag_chain, MockSlackApp):
    """
    Tests the full request/response cycle using the app factory pattern.
    """
    # Arrange: Configure mocks
    mock_rag_chain.invoke.return_value = "This is a test response."
    mock_app_instance = MockSlackApp.return_value

    # Arrange: Import and create the app. The factory will use our mocked App class.
    from app.factory import create_app

    app = create_app()
    client = TestClient(app)

    # Arrange: Define the event payload that simulates a user mentioning the bot.
    slack_event_payload = {
        "token": "a_verification_token",
        "team_id": "TXXXXXXXX",
        "api_app_id": "AXXXXXXXX",
        "event": {
            "type": "app_mention",
            "text": "<@UXXXXXXXXX> what is langchain?",
            "user": "UXXXXXXX",
            "channel": "CXXXXXXX",
        },
        "type": "event_callback",
    }

    # Act: POST the payload to the endpoint.
    response = client.post("/slack/events", json=slack_event_payload)

    # Assert: The server should acknowledge the request.
    assert response.status_code == 200

    # Assert: The handler registered via the decorator on our mock app was called.
    # This confirms the FastAPI -> SlackRequestHandler -> dispatcher wiring is correct.
    mock_app_instance.event.assert_called_with("app_mention")

    # Assert: Our own application logic was triggered correctly.
    mock_rag_chain.invoke.assert_called_once_with("what is langchain?")

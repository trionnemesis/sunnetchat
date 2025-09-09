import pytest
from unittest.mock import MagicMock

@pytest.fixture(autouse=True)
def prevent_slack_api_calls(monkeypatch):
    """
    A session-wide fixture, defined in conftest.py, to automatically prevent
    the slack_bolt.App from making real API calls during initialization in any test.
    This runs before any test collection happens.
    """
    def do_nothing_init(self, *args, **kwargs):
        # The original method in slack_bolt tries to make an API call.
        # We replace it with this to prevent that during tests.
        # We also need to set a dummy client on the instance, as other methods use it.
        self._client = MagicMock()

    from slack_bolt.app import App
    monkeypatch.setattr(App, "_init_middleware_list", do_nothing_init)

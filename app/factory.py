import os
import re
from fastapi import FastAPI
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

# This placeholder will be patched during tests
rag_chain = object()


def create_app() -> FastAPI:
    """
    Factory to create the FastAPI app and the Slack app.
    This isolates the creation process, making it testable.
    """
    # The App is now created inside the factory, not on module import
    slack_app = App(
        token=os.environ.get("SLACK_BOT_TOKEN", "xoxb-fake-token"),
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET", "fake-secret"),
    )

    # The handler function is defined inside the factory as well
    @slack_app.event("app_mention")
    def handle_app_mention(body: dict, say):
        text = body["event"]["text"]
        question = re.sub(r"<@.*?>", "", text).strip()
        answer = rag_chain.invoke(question)
        say(text=answer)

    fastapi_app = FastAPI()
    handler = SlackRequestHandler(slack_app)
    fastapi_app.add_api_route("/slack/events", handler.handle, methods=["POST"])
    return fastapi_app

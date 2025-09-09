# main.py

import os
from fastapi import FastAPI, Request, Response
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

# Import our agent graph
from .agent import graph

# --- FastAPI & Slack App Initialization ---
app = FastAPI()

slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

app_handler = AsyncSlackRequestHandler(slack_app)

# --- Slack Event Handlers ---

@slack_app.event("app_mention")
async def handle_app_mentions(body, say, logger):
    """ Handles mentions of the bot in any channel. """
    user_question = body["event"]["text"].split('>')[-1].strip()
    user_id = body["event"]["user"]
    
    logger.info(f"Received question from {user_id}: {user_question}")
    await say(f"Received your question, <@{user_id}>. Processing... :hourglass_flowing_sand:")

    # Invoke the LangGraph agent
    inputs = {"question": user_question}
    final_answer = "Sorry, I encountered an error while processing your request."
    
    try:
        # The final answer is in the last 'generation' field of the stream
        async for output in graph.astream(inputs):
            for key, value in output.items():
                logger.info(f"---Node: {key}---")
                # The final generation is the one we want to show
                if "generation" in value and value["generation"]:
                    final_answer = value["generation"]

    except Exception as e:
        logger.error(f"Error in agent execution: {e}")
        final_answer = f"An error occurred: {e}"

    await say(final_answer)

# --- FastAPI Webhook Endpoint ---

@app.post("/slack/events")
async def endpoint(req: Request):
    """ The main webhook for all Slack events. """
    return await app_handler.handle(req)

@app.get("/")
async def root():
    return {"status": "ok"}

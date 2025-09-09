# main.py

import os
import asyncio
from typing import Dict, Any
from fastapi import FastAPI, Request, Response, BackgroundTasks
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.fastapi.async_handler import AsyncSlackRequestHandler

# Import our unified core agent
from .core_agent import get_agent, TaskStatus

# --- FastAPI & Slack App Initialization ---
app = FastAPI()

slack_app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
)

app_handler = AsyncSlackRequestHandler(slack_app)

# --- Slack Event Handlers ---

# Store for tracking ongoing tasks
active_tasks: Dict[str, Dict[str, Any]] = {}


async def process_question_background(question: str, user_id: str, say_func, logger):
    """Background task for processing questions with progress updates"""
    task_id = f"{user_id}_{hash(question)}"

    try:
        # Initialize task tracking
        active_tasks[task_id] = {
            "status": TaskStatus.RUNNING,
            "progress": {"step": "starting"},
            "start_time": asyncio.get_event_loop().time(),
        }

        # Get agent instance
        agent = get_agent()

        # Process question with progress updates
        result = await agent.process_question(question)

        # Extract final answer
        final_answer = result.get("generation", "抱歉，我無法處理您的問題。")
        status = result.get("status", TaskStatus.FAILED)

        # Update task status
        active_tasks[task_id]["status"] = status
        active_tasks[task_id]["result"] = result

        # Send final response
        if status == TaskStatus.COMPLETED or final_answer:
            await say_func(f"<@{user_id}> {final_answer}")
        else:
            error_msg = result.get("error_message", "處理過程中發生未知錯誤")
            await say_func(f"<@{user_id}> 抱歉，處理您的問題時發生錯誤：{error_msg}")

        logger.info(f"Task {task_id} completed with status: {status}")

    except Exception as e:
        logger.error(f"Background task {task_id} failed: {e}")
        active_tasks[task_id]["status"] = TaskStatus.FAILED
        active_tasks[task_id]["error"] = str(e)

        await say_func(f"<@{user_id}> 抱歉，處理您的問題時發生了錯誤。請稍後再試。")

    finally:
        # Clean up task after completion
        if task_id in active_tasks:
            del active_tasks[task_id]


@slack_app.event("app_mention")
async def handle_app_mentions(body, say, logger):
    """Handles mentions of the bot with async background processing"""
    user_question = body["event"]["text"].split(">")[-1].strip()
    user_id = body["event"]["user"]
    channel_id = body["event"]["channel"]

    logger.info(f"Received question from {user_id} in {channel_id}: {user_question}")

    # Immediate acknowledgment
    await say(f"收到您的問題，<@{user_id}>！正在處理中... :hourglass_flowing_sand:")

    # Start background processing
    asyncio.create_task(
        process_question_background(user_question, user_id, say, logger)
    )


# --- FastAPI Webhook Endpoint ---


@app.post("/slack/events")
async def endpoint(req: Request):
    """The main webhook for all Slack events."""
    return await app_handler.handle(req)


@app.get("/")
async def root():
    return {"status": "ok"}

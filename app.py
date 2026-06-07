import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
Path("outputs").mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return f.read()


@app.post("/research")
async def research(request: Request):
    """Step 1 — research a topic and return 10 hooks to choose from."""
    from agents import hook_agent, youtube_research
    from agents.topic_bank import get_topic_for_today

    body = await request.json()
    topic = body.get("topic", "").strip() or get_topic_for_today()

    yt_data = await asyncio.to_thread(youtube_research.run, topic)
    hook_data = await asyncio.to_thread(hook_agent.run, topic, yt_data.get("forum_research", ""))

    return {
        "topic": topic,
        "hooks": hook_data["hooks"],
        "research_summary": yt_data.get("forum_research", ""),
    }


@app.post("/write")
async def write(request: Request):
    """Step 2 — write a script around the chosen hook."""
    from agents import script_writer, youtube_research

    body = await request.json()
    topic = body.get("topic", "").strip()
    hook = body.get("hook", "").strip()
    if not topic or not hook:
        return {"error": "topic and hook required"}

    yt_data = await asyncio.to_thread(youtube_research.run, topic)
    script_data = await asyncio.to_thread(script_writer.run, topic, yt_data, winning_hook=hook)

    return {"script": script_data["script"]}

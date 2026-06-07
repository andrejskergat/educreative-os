import asyncio
import logging
import traceback
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
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
    from agents import hook_agent, youtube_research
    from agents.topic_bank import get_topic_for_today

    try:
        body = await request.json()
        topic = body.get("topic", "").strip() or get_topic_for_today()

        yt_data = await asyncio.to_thread(youtube_research.run, topic)
        hook_data = await asyncio.to_thread(hook_agent.run, topic, yt_data.get("forum_research", ""))

        return JSONResponse({
            "topic": topic,
            "hooks": hook_data["hooks"],
        })
    except Exception as e:
        logger.error(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/write")
async def write(request: Request):
    from agents import script_writer, youtube_research

    try:
        body = await request.json()
        topic = body.get("topic", "").strip()
        hook = body.get("hook", "").strip()
        if not topic or not hook:
            return JSONResponse({"error": "topic and hook required"}, status_code=400)

        yt_data = await asyncio.to_thread(youtube_research.run, topic)
        script_data = await asyncio.to_thread(script_writer.run, topic, yt_data, winning_hook=hook)

        return JSONResponse({"script": script_data["script"]})
    except Exception as e:
        logger.error(traceback.format_exc())
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/topics")
async def topics():
    try:
        from agents.topic_bank import get_topic_for_today
        return JSONResponse({"today": get_topic_for_today()})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

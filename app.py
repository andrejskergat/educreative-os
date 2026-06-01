import asyncio
import json
import logging
import os
import sqlite3
import traceback
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

DB = "jobs.db"


def init_db():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            topic TEXT,
            status TEXT,
            created_at TEXT,
            script TEXT,
            thumbnail TEXT,
            canva_url TEXT,
            description TEXT,
            research TEXT,
            youtube_data TEXT,
            script_context TEXT,
            thumbnail_context TEXT
        )
    """)
    con.commit()
    con.close()


init_db()


def db_get(job_id: str):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def db_update(job_id: str, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [job_id]
    con = sqlite3.connect(DB)
    con.execute(f"UPDATE jobs SET {fields} WHERE id=?", values)
    con.commit()
    con.close()


def db_list():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


_queues: dict[str, asyncio.Queue] = {}


async def send_event(job_id: str, event: str, data: str):
    if job_id in _queues:
        await _queues[job_id].put(f"event: {event}\ndata: {data}\n\n")


async def run_pipeline_async(job_id: str, topic: str, script_context: str = ""):
    from agents import script_writer, youtube_research

    try:
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Researching topic..."}))
        db_update(job_id, status="researching")
        yt_data = await asyncio.to_thread(youtube_research.run, topic)
        db_update(job_id, youtube_data=json.dumps(yt_data), research=yt_data.get("forum_research", ""))
        video_count = len(yt_data.get("videos", []))
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": f"Research done — {video_count} videos + community insights", "done": True}))

        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Writing script..."}))
        db_update(job_id, status="scripting")
        script_data = await asyncio.to_thread(script_writer.run, topic, yt_data, script_context)
        db_update(job_id, script=script_data["script"])
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Script written", "done": True}))

        db_update(job_id, status="done")
        await send_event(job_id, "done", json.dumps({"job_id": job_id}))

    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"[{job_id}] Pipeline failed: {error_msg}")
        db_update(job_id, status="error")
        await send_event(job_id, "error", json.dumps({"msg": str(e)}))
    finally:
        await asyncio.sleep(5)
        _queues.pop(job_id, None)


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("static/index.html") as f:
        return f.read()


@app.post("/jobs")
async def create_job(request: Request):
    body = await request.json()
    topic = body.get("topic", "").strip()
    if not topic:
        return {"error": "topic required"}
    script_context = body.get("script_context", "")
    thumbnail_context = body.get("thumbnail_context", "")
    job_id = str(uuid.uuid4())[:8]
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO jobs (id, topic, status, created_at, script_context, thumbnail_context) VALUES (?,?,?,?,?,?)",
        (job_id, topic, "queued", datetime.now().isoformat(), script_context, thumbnail_context),
    )
    con.commit()
    con.close()
    _queues[job_id] = asyncio.Queue()
    asyncio.create_task(run_pipeline_async(job_id, topic, script_context))
    return {"job_id": job_id}


@app.post("/jobs/{job_id}/thumbnail")
async def generate_thumbnail(job_id: str):
    from agents import thumbnail_agent
    job = db_get(job_id)
    if not job or not job.get("script"):
        return {"error": "job not found or script not ready"}
    db_update(job_id, status="thumbnail")
    try:
        thumb_data = await asyncio.to_thread(
            thumbnail_agent.run, job["topic"], job["script"], job.get("thumbnail_context", "")
        )
        db_update(job_id, thumbnail=thumb_data["thumbnail_concept"], canva_url=thumb_data.get("canva_url", ""), status="done")
    except Exception as e:
        db_update(job_id, status="done")
        return {"error": str(e)}
    return db_get(job_id)


@app.post("/jobs/{job_id}/description")
async def generate_description(job_id: str):
    from agents import description_agent
    job = db_get(job_id)
    if not job or not job.get("script"):
        return {"error": "job not found or script not ready"}
    db_update(job_id, status="description")
    try:
        desc_data = await asyncio.to_thread(
            description_agent.run, job["topic"], job["script"]
        )
        db_update(job_id, description=desc_data["description"], status="done")
    except Exception as e:
        db_update(job_id, status="done")
        return {"error": str(e)}
    return db_get(job_id)


@app.get("/jobs")
async def list_jobs():
    return db_list()


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    return db_get(job_id)


@app.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    queue = _queues.get(job_id)
    if not queue:
        job = db_get(job_id)
        if job and job["status"] == "done":
            async def already_done():
                yield f"event: done\ndata: {json.dumps({'job_id': job_id})}\n\n"
            return StreamingResponse(already_done(), media_type="text/event-stream")
        return {"error": "job not found or not running"}

    async def event_stream():
        while True:
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=30)
                yield msg
                if msg.startswith("event: done") or msg.startswith("event: error"):
                    break
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/outputs/{job_id}.txt")
async def download_output(job_id: str):
    path = Path("outputs") / f"{job_id}.txt"
    if path.exists():
        return FileResponse(path, filename=f"educreative-{job_id}.txt")
    return {"error": "not found"}

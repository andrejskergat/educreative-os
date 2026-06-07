import asyncio
import json
import logging
import os
import sqlite3
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import httpx
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
            thumbnail_context TEXT,
            hook_variants TEXT,
            winning_hook TEXT,
            is_daily INTEGER DEFAULT 0
        )
    """)
    # migrate existing tables that lack the new columns
    for col, definition in [
        ("hook_variants", "TEXT"),
        ("winning_hook", "TEXT"),
        ("is_daily", "INTEGER DEFAULT 0"),
    ]:
        try:
            con.execute(f"ALTER TABLE jobs ADD COLUMN {col} {definition}")
        except Exception:
            pass
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
    from agents import hook_agent, script_writer, youtube_research

    try:
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Researching topic..."}))
        db_update(job_id, status="researching")
        yt_data = await asyncio.to_thread(youtube_research.run, topic)
        db_update(job_id, youtube_data=json.dumps(yt_data), research=yt_data.get("forum_research", ""))
        video_count = len(yt_data.get("videos", []))
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": f"Research done — {video_count} videos + community insights", "done": True}))

        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Crafting hooks..."}))
        db_update(job_id, status="hooks")
        hook_data = await asyncio.to_thread(hook_agent.run, topic, yt_data.get("forum_research", ""))
        db_update(job_id, hook_variants=hook_data["hook_variants"], winning_hook=hook_data["winning_hook"])
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Best hook selected", "done": True}))

        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Writing script..."}))
        db_update(job_id, status="scripting")
        script_data = await asyncio.to_thread(
            script_writer.run, topic, yt_data, script_context, hook_data["winning_hook"]
        )
        db_update(job_id, script=script_data["script"])
        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Script written", "done": True}))

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
    is_daily = 1 if body.get("is_daily") else 0
    job_id = str(uuid.uuid4())[:8]
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO jobs (id, topic, status, created_at, script_context, thumbnail_context, is_daily) VALUES (?,?,?,?,?,?,?)",
        (job_id, topic, "queued", datetime.now().isoformat(), script_context, thumbnail_context, is_daily),
    )
    con.commit()
    con.close()
    _queues[job_id] = asyncio.Queue()
    asyncio.create_task(run_pipeline_async(job_id, topic, script_context))
    return {"job_id": job_id}


@app.post("/daily")
async def generate_daily_script():
    """Generate today's daily script from the topic bank."""
    from agents.topic_bank import get_topic_for_today
    topic = get_topic_for_today()
    # Check if we already generated one for today
    today_str = datetime.now().date().isoformat()
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    existing = con.execute(
        "SELECT * FROM jobs WHERE is_daily=1 AND created_at LIKE ? ORDER BY created_at DESC LIMIT 1",
        (f"{today_str}%",)
    ).fetchone()
    con.close()
    if existing:
        return {"job_id": existing["id"], "topic": existing["topic"], "already_exists": True}

    job_id = str(uuid.uuid4())[:8]
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO jobs (id, topic, status, created_at, script_context, thumbnail_context, is_daily) VALUES (?,?,?,?,?,?,?)",
        (job_id, topic, "queued", datetime.now().isoformat(), "", "", 1),
    )
    con.commit()
    con.close()
    _queues[job_id] = asyncio.Queue()
    asyncio.create_task(run_pipeline_async(job_id, topic))
    return {"job_id": job_id, "topic": topic, "already_exists": False}


@app.get("/topics")
async def list_topics():
    """Return all topics in the bank with today's topic highlighted."""
    from agents.topic_bank import get_all_topics, get_topic_for_today
    today_topic = get_topic_for_today()
    topics = get_all_topics()
    return {"today": today_topic, "topics": topics}


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


# ── GitHub Actions integration ────────────────────────────────────────────────

GH_REPO = os.getenv("GITHUB_REPO", "andrejskergat/educreative-os")
GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
GH_WORKFLOW = "daily-script.yml"
GH_BRANCH = "main"


async def _gh(method: str, path: str, body: dict | None = None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GH_TOKEN:
        headers["Authorization"] = f"Bearer {GH_TOKEN}"
    url = f"https://api.github.com{path}"
    async with httpx.AsyncClient(timeout=15) as client:
        fn = getattr(client, method)
        resp = await fn(url, headers=headers, **({"json": body} if body else {}))
    return resp


@app.post("/gh/trigger")
async def gh_trigger(request: Request):
    """Trigger the GitHub Actions daily script workflow."""
    body = await request.json()
    topic_override = body.get("topic_override", "")
    payload = {
        "ref": GH_BRANCH,
        "inputs": {"topic_override": topic_override},
    }
    resp = await _gh("post", f"/repos/{GH_REPO}/actions/workflows/{GH_WORKFLOW}/dispatches", payload)
    if resp.status_code == 204:
        return {"ok": True}
    return {"ok": False, "status": resp.status_code, "detail": resp.text}


@app.get("/gh/runs")
async def gh_runs():
    """List recent workflow runs."""
    resp = await _gh("get", f"/repos/{GH_REPO}/actions/workflows/{GH_WORKFLOW}/runs?per_page=10")
    if resp.status_code != 200:
        return {"runs": [], "error": resp.text}
    data = resp.json()
    runs = [
        {
            "id": r["id"],
            "status": r["status"],
            "conclusion": r["conclusion"],
            "created_at": r["created_at"],
            "html_url": r["html_url"],
            "name": r.get("display_title", r.get("name", "")),
        }
        for r in data.get("workflow_runs", [])
    ]
    return {"runs": runs}


@app.get("/gh/scripts")
async def gh_scripts():
    """List generated scripts from the scripts/ folder in the repo."""
    resp = await _gh("get", f"/repos/{GH_REPO}/contents/scripts")
    if resp.status_code == 404:
        return {"scripts": []}
    if resp.status_code != 200:
        return {"scripts": [], "error": resp.text}
    files = [
        {"name": f["name"], "path": f["path"], "download_url": f["download_url"]}
        for f in resp.json()
        if f["name"].endswith(".md")
    ]
    files.sort(key=lambda x: x["name"], reverse=True)
    return {"scripts": files}


@app.get("/gh/scripts/{filename}")
async def gh_script_content(filename: str):
    """Fetch content of a specific script file."""
    resp = await _gh("get", f"/repos/{GH_REPO}/contents/scripts/{filename}")
    if resp.status_code != 200:
        return {"error": "not found"}
    import base64
    content = base64.b64decode(resp.json()["content"]).decode("utf-8")
    return {"filename": filename, "content": content}

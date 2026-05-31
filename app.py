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
            thumbnail_url TEXT,
            description TEXT,
            youtube_data TEXT,
            script_context TEXT,
            thumbnail_context TEXT,
            error TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS ad_jobs (
            id TEXT PRIMARY KEY,
            product TEXT,
            platform TEXT,
            status TEXT,
            created_at TEXT,
            research TEXT,
            ad_copy TEXT,
            creative_concepts TEXT,
            audience_brief TEXT,
            canva_url TEXT,
            copy_context TEXT,
            creative_context TEXT,
            error TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS meta_ad_jobs (
            id TEXT PRIMARY KEY,
            product TEXT,
            niche TEXT,
            angle TEXT,
            country TEXT,
            status TEXT,
            created_at TEXT,
            research TEXT,
            competitor_ads TEXT,
            best_ads TEXT,
            competitor_analysis TEXT,
            ad_copy TEXT,
            creative_concepts TEXT,
            canva_designs TEXT,
            audience_brief TEXT,
            copy_context TEXT,
            creative_context TEXT,
            error TEXT
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


async def run_pipeline_async(job_id: str, topic: str, script_context: str = "", thumbnail_context: str = ""):
    from agents import description_agent, script_writer, thumbnail_agent, youtube_research

    try:
        logger.info(f"[{job_id}] Starting YouTube research for: {topic}")
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Running YouTube Research..."}))
        db_update(job_id, status="researching")
        yt_data = await asyncio.to_thread(youtube_research.run, topic)
        db_update(job_id, youtube_data=json.dumps(yt_data))
        logger.info(f"[{job_id}] YouTube research done. {len(yt_data['videos'])} videos found.")
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": f"Found {len(yt_data['videos'])} videos", "done": True}))

        logger.info(f"[{job_id}] Starting script writer")
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Writing script..."}))
        db_update(job_id, status="scripting")
        script_data = await asyncio.to_thread(script_writer.run, topic, yt_data, script_context)
        db_update(job_id, script=script_data["script"])
        logger.info(f"[{job_id}] Script done.")
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Script written", "done": True}))

        logger.info(f"[{job_id}] Starting thumbnail agent")
        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Designing thumbnail..."}))
        db_update(job_id, status="thumbnail")
        thumb_data = await asyncio.to_thread(thumbnail_agent.run, topic, script_data["script"], thumbnail_context)
        db_update(job_id, thumbnail=thumb_data["thumbnail_concept"], canva_url=thumb_data.get("canva_url", ""))
        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Thumbnail ready", "done": True}))

        logger.info(f"[{job_id}] Starting description agent")
        await send_event(job_id, "progress", json.dumps({"step": 4, "msg": "Writing description & hashtags..."}))
        db_update(job_id, status="description")
        desc_data = await asyncio.to_thread(description_agent.run, topic, script_data["script"])
        db_update(job_id, description=desc_data["description"])
        logger.info(f"[{job_id}] Description done.")
        await send_event(job_id, "progress", json.dumps({"step": 4, "msg": "Description ready", "done": True}))

        output_path = Path("outputs") / f"{job_id}.txt"
        job = db_get(job_id)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"TOPIC: {topic}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("=" * 60 + "\nSCRIPT\n" + "=" * 60 + "\n")
            f.write(job["script"] + "\n\n")
            f.write("=" * 60 + "\nTHUMBNAIL CONCEPT\n" + "=" * 60 + "\n")
            f.write(job["thumbnail"] + "\n\n")
            f.write("=" * 60 + "\nDESCRIPTION & HASHTAGS\n" + "=" * 60 + "\n")
            f.write(job["description"] + "\n")

        db_update(job_id, status="done")
        logger.info(f"[{job_id}] Pipeline complete.")
        await send_event(job_id, "done", json.dumps({"job_id": job_id}))

    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"[{job_id}] Pipeline failed: {error_msg}")
        db_update(job_id, status="error", error=str(e))
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
    asyncio.create_task(run_pipeline_async(job_id, topic, script_context, thumbnail_context))
    return {"job_id": job_id}


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


# ── Ad Jobs ──────────────────────────────────────────────────────────────────

def ad_db_get(job_id: str):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM ad_jobs WHERE id=?", (job_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def ad_db_update(job_id: str, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [job_id]
    con = sqlite3.connect(DB)
    con.execute(f"UPDATE ad_jobs SET {fields} WHERE id=?", values)
    con.commit()
    con.close()


def ad_db_list():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM ad_jobs ORDER BY created_at DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


async def run_ad_pipeline_async(
    job_id: str,
    product: str,
    platform: str,
    copy_context: str = "",
    creative_context: str = "",
):
    from agents import ad_research, ad_copy_writer, ad_creative_agent, ad_audience_agent

    try:
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Researching winning angles..."}))
        ad_db_update(job_id, status="researching")
        research_data = await asyncio.to_thread(ad_research.run, product, platform)
        ad_db_update(job_id, research=research_data["research"])
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Research complete", "done": True}))

        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "Writing ad copy variants..."}))
        ad_db_update(job_id, status="copywriting")
        copy_data = await asyncio.to_thread(
            ad_copy_writer.run, product, research_data["research"], platform, copy_context
        )
        ad_db_update(job_id, ad_copy=copy_data["ad_copy"])
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": "3 copy variants ready", "done": True}))

        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Designing creative concepts..."}))
        ad_db_update(job_id, status="creative")
        creative_data = await asyncio.to_thread(
            ad_creative_agent.run, product, copy_data["ad_copy"], platform, creative_context
        )
        ad_db_update(
            job_id,
            creative_concepts=creative_data["creative_concepts"],
            canva_url=creative_data.get("canva_url", ""),
        )
        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Creative concepts ready", "done": True}))

        await send_event(job_id, "progress", json.dumps({"step": 4, "msg": "Building audience brief..."}))
        ad_db_update(job_id, status="audience")
        audience_data = await asyncio.to_thread(
            ad_audience_agent.run, product, research_data["research"], platform
        )
        ad_db_update(job_id, audience_brief=audience_data["audience_brief"])
        await send_event(job_id, "progress", json.dumps({"step": 4, "msg": "Audience brief ready", "done": True}))

        output_path = Path("outputs") / f"ad-{job_id}.txt"
        job = ad_db_get(job_id)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"PRODUCT/OFFER: {product}\n")
            f.write(f"PLATFORM: {platform}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("=" * 60 + "\nAD RESEARCH & ANGLES\n" + "=" * 60 + "\n")
            f.write(job["research"] + "\n\n")
            f.write("=" * 60 + "\nAD COPY VARIANTS\n" + "=" * 60 + "\n")
            f.write(job["ad_copy"] + "\n\n")
            f.write("=" * 60 + "\nCREATIVE CONCEPTS\n" + "=" * 60 + "\n")
            f.write(job["creative_concepts"] + "\n\n")
            f.write("=" * 60 + "\nAUDIENCE BRIEF\n" + "=" * 60 + "\n")
            f.write(job["audience_brief"] + "\n")

        ad_db_update(job_id, status="done")
        await send_event(job_id, "done", json.dumps({"job_id": job_id}))

    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"[ad-{job_id}] Pipeline failed: {error_msg}")
        ad_db_update(job_id, status="error", error=str(e))
        await send_event(job_id, "error", json.dumps({"msg": str(e)}))
    finally:
        await asyncio.sleep(5)
        _queues.pop(job_id, None)


@app.post("/ad-jobs")
async def create_ad_job(request: Request):
    body = await request.json()
    product = body.get("product", "").strip()
    if not product:
        return {"error": "product required"}
    platform = body.get("platform", "Meta").strip()
    copy_context = body.get("copy_context", "")
    creative_context = body.get("creative_context", "")
    job_id = str(uuid.uuid4())[:8]
    con = sqlite3.connect(DB)
    con.execute(
        "INSERT INTO ad_jobs (id, product, platform, status, created_at, copy_context, creative_context) VALUES (?,?,?,?,?,?,?)",
        (job_id, product, platform, "queued", datetime.now().isoformat(), copy_context, creative_context),
    )
    con.commit()
    con.close()
    _queues[job_id] = asyncio.Queue()
    asyncio.create_task(run_ad_pipeline_async(job_id, product, platform, copy_context, creative_context))
    return {"job_id": job_id}


@app.get("/ad-jobs")
async def list_ad_jobs():
    return ad_db_list()


@app.get("/ad-jobs/{job_id}")
async def get_ad_job(job_id: str):
    return ad_db_get(job_id)


@app.get("/ad-jobs/{job_id}/stream")
async def stream_ad_job(job_id: str):
    queue = _queues.get(job_id)
    if not queue:
        job = ad_db_get(job_id)
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


@app.get("/outputs/ad-{job_id}.txt")
async def download_ad_output(job_id: str):
    path = Path("outputs") / f"ad-{job_id}.txt"
    if path.exists():
        return FileResponse(path, filename=f"educreative-ad-{job_id}.txt")
    return {"error": "not found"}


# ── Meta Ad Jobs ──────────────────────────────────────────────────────────────

def meta_db_get(job_id: str):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    row = con.execute("SELECT * FROM meta_ad_jobs WHERE id=?", (job_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def meta_db_update(job_id: str, **kwargs):
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [job_id]
    con = sqlite3.connect(DB)
    con.execute(f"UPDATE meta_ad_jobs SET {fields} WHERE id=?", values)
    con.commit()
    con.close()


def meta_db_list():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM meta_ad_jobs ORDER BY created_at DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


async def run_meta_ad_pipeline_async(
    job_id: str,
    product: str,
    niche: str,
    angle: str,
    country: str,
    copy_context: str = "",
    creative_context: str = "",
):
    from agents import (
        ad_research,
        meta_ads_library,
        meta_ads_analyzer,
        ad_copy_writer,
        ad_creative_agent,
        canva_creator,
        ad_audience_agent,
    )

    try:
        # Step 1 — General niche research
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Researching niche angles..."}))
        meta_db_update(job_id, status="researching")
        research_data = await asyncio.to_thread(ad_research.run, product, "Meta")
        meta_db_update(job_id, research=research_data["research"])
        await send_event(job_id, "progress", json.dumps({"step": 1, "msg": "Niche research done", "done": True}))

        # Step 2 — Fetch competitor ads from Meta Ads Library
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": f"Fetching competitor ads for '{niche}'..."}))
        meta_db_update(job_id, status="fetching_ads")
        library_data = await asyncio.to_thread(meta_ads_library.run, niche, country)
        meta_db_update(job_id, competitor_ads=json.dumps(library_data))
        total = library_data.get("total", 0)
        err = library_data.get("error", "")
        msg = f"Found {total} competitor ads" if not err else f"Ads Library: {err[:80]}"
        await send_event(job_id, "progress", json.dumps({"step": 2, "msg": msg, "done": True}))

        # Step 3 — Analyze and rank best ads
        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": "Analyzing best-performing ads..."}))
        meta_db_update(job_id, status="analyzing")
        analyzer_data = await asyncio.to_thread(meta_ads_analyzer.run, library_data)
        meta_db_update(
            job_id,
            best_ads=json.dumps(analyzer_data["best_ads"]),
            competitor_analysis=analyzer_data["analysis"],
        )
        await send_event(job_id, "progress", json.dumps({"step": 3, "msg": f"Analyzed top {analyzer_data['total_shown']} ads", "done": True}))

        # Step 4 — Write ad copy variants grounded in the angle + competitor intel
        await send_event(job_id, "progress", json.dumps({"step": 4, "msg": "Writing ad copy variants..."}))
        meta_db_update(job_id, status="copywriting")
        copy_data = await asyncio.to_thread(
            ad_copy_writer.run,
            product,
            research_data["research"],
            "Meta",
            copy_context,
            angle,
            analyzer_data["analysis"],
        )
        meta_db_update(job_id, ad_copy=copy_data["ad_copy"])
        await send_event(job_id, "progress", json.dumps({"step": 4, "msg": "3 copy variants ready", "done": True}))

        # Step 5 — Creative strategy
        await send_event(job_id, "progress", json.dumps({"step": 5, "msg": "Designing creative concepts..."}))
        meta_db_update(job_id, status="creative")
        creative_data = await asyncio.to_thread(
            ad_creative_agent.run,
            product,
            copy_data["ad_copy"],
            "Meta",
            creative_context,
            analyzer_data["analysis"],
        )
        meta_db_update(job_id, creative_concepts=creative_data["creative_concepts"])
        await send_event(job_id, "progress", json.dumps({"step": 5, "msg": "Creative concepts ready", "done": True}))

        # Step 6 — Create Canva designs
        await send_event(job_id, "progress", json.dumps({"step": 6, "msg": "Creating Canva designs..."}))
        meta_db_update(job_id, status="canva")
        canva_data = await asyncio.to_thread(
            canva_creator.run,
            product,
            creative_data.get("canva_prompts", []),
            copy_data["ad_copy"],
        )
        meta_db_update(job_id, canva_designs=json.dumps(canva_data["designs"]))
        count = canva_data.get("successful_count", 0)
        note = canva_data.get("note", "")
        msg = f"{count} Canva design(s) created" if count else (note or "Canva skipped")
        await send_event(job_id, "progress", json.dumps({"step": 6, "msg": msg, "done": True}))

        # Step 7 — Audience brief
        await send_event(job_id, "progress", json.dumps({"step": 7, "msg": "Building audience targeting brief..."}))
        meta_db_update(job_id, status="audience")
        audience_data = await asyncio.to_thread(
            ad_audience_agent.run, product, research_data["research"], "Meta"
        )
        meta_db_update(job_id, audience_brief=audience_data["audience_brief"])
        await send_event(job_id, "progress", json.dumps({"step": 7, "msg": "Audience brief ready", "done": True}))

        # Write output file
        output_path = Path("outputs") / f"meta-{job_id}.txt"
        job = meta_db_get(job_id)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"PRODUCT: {product}\n")
            f.write(f"NICHE: {niche} | ANGLE: {angle} | COUNTRY: {country}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write("=" * 60 + "\nCOMPETITOR ANALYSIS\n" + "=" * 60 + "\n")
            f.write(job["competitor_analysis"] + "\n\n")
            f.write("=" * 60 + "\nAD COPY VARIANTS\n" + "=" * 60 + "\n")
            f.write(job["ad_copy"] + "\n\n")
            f.write("=" * 60 + "\nCREATIVE CONCEPTS\n" + "=" * 60 + "\n")
            f.write(job["creative_concepts"] + "\n\n")
            f.write("=" * 60 + "\nAUDIENCE BRIEF\n" + "=" * 60 + "\n")
            f.write(job["audience_brief"] + "\n")

        meta_db_update(job_id, status="done")
        logger.info(f"[meta-{job_id}] Pipeline complete.")
        await send_event(job_id, "done", json.dumps({"job_id": job_id}))

    except Exception as e:
        error_msg = traceback.format_exc()
        logger.error(f"[meta-{job_id}] Pipeline failed: {error_msg}")
        meta_db_update(job_id, status="error", error=str(e))
        await send_event(job_id, "error", json.dumps({"msg": str(e)}))
    finally:
        await asyncio.sleep(5)
        _queues.pop(job_id, None)


@app.post("/meta-ad-jobs")
async def create_meta_ad_job(request: Request):
    body = await request.json()
    product = body.get("product", "").strip()
    niche = body.get("niche", "").strip()
    if not product or not niche:
        return {"error": "product and niche are required"}
    angle = body.get("angle", "").strip()
    country = body.get("country", "AU").strip()
    copy_context = body.get("copy_context", "")
    creative_context = body.get("creative_context", "")
    job_id = str(uuid.uuid4())[:8]
    con = sqlite3.connect(DB)
    con.execute(
        """INSERT INTO meta_ad_jobs
           (id, product, niche, angle, country, status, created_at, copy_context, creative_context)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (job_id, product, niche, angle, country, "queued", datetime.now().isoformat(), copy_context, creative_context),
    )
    con.commit()
    con.close()
    _queues[job_id] = asyncio.Queue()
    asyncio.create_task(
        run_meta_ad_pipeline_async(job_id, product, niche, angle, country, copy_context, creative_context)
    )
    return {"job_id": job_id}


@app.get("/meta-ad-jobs")
async def list_meta_ad_jobs():
    return meta_db_list()


@app.get("/meta-ad-jobs/{job_id}")
async def get_meta_ad_job(job_id: str):
    return meta_db_get(job_id)


@app.get("/meta-ad-jobs/{job_id}/stream")
async def stream_meta_ad_job(job_id: str):
    queue = _queues.get(job_id)
    if not queue:
        job = meta_db_get(job_id)
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


@app.get("/outputs/meta-{job_id}.txt")
async def download_meta_ad_output(job_id: str):
    path = Path("outputs") / f"meta-{job_id}.txt"
    if path.exists():
        return FileResponse(path, filename=f"educreative-meta-{job_id}.txt")
    return {"error": "not found"}

import os
import time
import httpx

CANVA_BASE = "https://api.canva.com/rest/v1"

# Meta ad format presets — Canva design type names
FORMATS = [
    {"name": "Feed Post (1:1)", "preset": "InstagramPost", "query": "facebook ad square"},
    {"name": "Story / Reel (9:16)", "preset": "InstagramStory", "query": "instagram story ad vertical"},
    {"name": "Feed Landscape (1.91:1)", "preset": "FacebookAd", "query": "facebook ad landscape"},
]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _search_brand_template(token: str, query: str) -> str | None:
    try:
        resp = httpx.get(
            f"{CANVA_BASE}/brand-templates",
            headers=_headers(token),
            params={"query": query, "limit": 5},
            timeout=15,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            return items[0]["id"]
    except Exception:
        pass
    return None


def _create_from_brand_template(token: str, template_id: str, title: str) -> str | None:
    try:
        resp = httpx.post(
            f"{CANVA_BASE}/designs",
            headers=_headers(token),
            json={
                "brand_template_id": template_id,
                "title": title,
            },
            timeout=30,
        )
        resp.raise_for_status()
        design = resp.json().get("design", {})
        design_id = design.get("id")
        if design_id:
            return f"https://www.canva.com/design/{design_id}/edit"
    except Exception:
        pass
    return None


def _create_blank_design(token: str, preset: str, title: str) -> str | None:
    try:
        resp = httpx.post(
            f"{CANVA_BASE}/designs",
            headers=_headers(token),
            json={
                "design_type": {"type": "preset", "name": preset},
                "title": title,
            },
            timeout=30,
        )
        resp.raise_for_status()
        design = resp.json().get("design", {})
        design_id = design.get("id")
        if design_id:
            return f"https://www.canva.com/design/{design_id}/edit"
    except Exception:
        pass
    return None


def run(product: str, canva_prompts: list[str], ad_copy: str) -> dict:
    """
    Create Canva designs for each Meta ad format.
    Tries brand templates first, falls back to blank designs in the correct format.
    Returns a list of {format, url, prompt} dicts.
    """
    token = os.getenv("CANVA_API_TOKEN")
    if not token:
        return {
            "designs": [],
            "note": "CANVA_API_TOKEN not set — designs skipped. Add it to env vars to enable.",
        }

    designs = []

    for i, fmt in enumerate(FORMATS):
        title = f"{product[:40]} — {fmt['name']}"
        url = None

        # 1. Try matching brand template
        template_id = _search_brand_template(token, fmt["query"])
        if template_id:
            url = _create_from_brand_template(token, template_id, title)

        # 2. Fall back to blank design in correct format
        if not url:
            url = _create_blank_design(token, fmt["preset"], title)

        canva_prompt = canva_prompts[i] if i < len(canva_prompts) else ""

        designs.append({
            "format": fmt["name"],
            "url": url,
            "canva_prompt": canva_prompt,
        })

    successful = [d for d in designs if d["url"]]
    return {
        "designs": designs,
        "successful_count": len(successful),
    }

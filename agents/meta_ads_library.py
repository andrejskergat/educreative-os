import os
import httpx
from datetime import datetime, timezone


GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

AD_FIELDS = ",".join([
    "id",
    "page_name",
    "page_id",
    "ad_creative_bodies",
    "ad_creative_link_titles",
    "ad_creative_link_descriptions",
    "ad_creative_link_captions",
    "ad_delivery_start_time",
    "ad_delivery_stop_time",
    "ad_snapshot_url",
    "publisher_platforms",
    "languages",
    "currency",
])


def _days_active(start_str: str, stop_str: str | None) -> int:
    try:
        fmt = "%Y-%m-%dT%H:%M:%S%z"
        start = datetime.strptime(start_str, fmt)
        end = datetime.strptime(stop_str, fmt) if stop_str else datetime.now(timezone.utc)
        return max(0, (end - start).days)
    except Exception:
        return 0


def run(niche: str, country: str = "AU", limit: int = 50) -> dict:
    """Fetch active competitor ads from Meta Ads Library for a given niche."""
    access_token = os.getenv("META_ACCESS_TOKEN")
    if not access_token:
        return {
            "ads": [],
            "total": 0,
            "error": "META_ACCESS_TOKEN not set — add it to your environment variables.",
        }

    params = {
        "access_token": access_token,
        "ad_reached_countries": f'["{country}"]',
        "search_terms": niche,
        "ad_active_status": "ACTIVE",
        "fields": AD_FIELDS,
        "limit": min(limit, 100),
    }

    try:
        resp = httpx.get(f"{GRAPH_API_BASE}/ads_archive", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except httpx.HTTPStatusError as e:
        return {"ads": [], "total": 0, "error": f"Meta API error: {e.response.text[:300]}"}
    except Exception as e:
        return {"ads": [], "total": 0, "error": str(e)}

    raw_ads = data.get("data", [])
    ads = []

    for item in raw_ads:
        bodies = item.get("ad_creative_bodies") or []
        titles = item.get("ad_creative_link_titles") or []
        descriptions = item.get("ad_creative_link_descriptions") or []
        captions = item.get("ad_creative_link_captions") or []
        start = item.get("ad_delivery_start_time", "")
        stop = item.get("ad_delivery_stop_time")
        days = _days_active(start, stop)
        platforms = item.get("publisher_platforms") or []

        # Infer ad type from platforms and caption patterns
        ad_type = "Feed Ad"
        caption_text = " ".join(captions).lower()
        if "wa.me" in caption_text or "whatsapp" in caption_text:
            ad_type = "WhatsApp"
        elif any(p in platforms for p in ["instagram"]) and not any(p in platforms for p in ["facebook"]):
            ad_type = "Instagram Feed"
        elif "facebook.com/events" in caption_text:
            ad_type = "Event"
        elif len(platforms) > 1:
            ad_type = "Multi-platform"

        ads.append({
            "id": item.get("id"),
            "page_name": item.get("page_name", "Unknown"),
            "body": bodies[0] if bodies else "",
            "headline": titles[0] if titles else "",
            "description": descriptions[0] if descriptions else "",
            "caption": captions[0] if captions else "",
            "ad_type": ad_type,
            "days_active": days,
            "start_date": start,
            "still_active": stop is None,
            "snapshot_url": item.get("ad_snapshot_url", ""),
            "platforms": platforms,
        })

    return {"ads": ads, "total": len(ads), "niche": niche, "country": country}

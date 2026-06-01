import os
import httpx
import anthropic


def run(product: str, platform: str = "Meta") -> dict:
    """Research winning angles and messaging for ads in this niche."""
    api_key = os.getenv("YOUTUBE_API_KEY")

    videos = []
    if api_key:
        try:
            base = "https://www.googleapis.com/youtube/v3"
            search_resp = httpx.get(f"{base}/search", params={
                "q": f"{product} ad campaign edtech",
                "part": "snippet",
                "type": "video",
                "maxResults": 10,
                "order": "viewCount",
                "key": api_key,
            }, timeout=15)
            search_resp.raise_for_status()
            items = search_resp.json().get("items", [])
            video_ids = [item["id"]["videoId"] for item in items if item.get("id", {}).get("videoId")]

            if video_ids:
                stats_resp = httpx.get(f"{base}/videos", params={
                    "part": "statistics,snippet",
                    "id": ",".join(video_ids),
                    "key": api_key,
                }, timeout=15)
                stats_resp.raise_for_status()
                for item in stats_resp.json().get("items", []):
                    videos.append({
                        "title": item["snippet"]["title"],
                        "channel": item["snippet"]["channelTitle"],
                        "views": int(item["statistics"].get("viewCount", 0)),
                        "description": item["snippet"]["description"][:300],
                    })
                videos.sort(key=lambda x: x["views"], reverse=True)
        except Exception:
            pass

    client = anthropic.Anthropic()

    video_context = ""
    if videos:
        video_context = "\n\nTOP PERFORMING CONTENT IN THIS NICHE:\n" + "\n".join([
            f"- \"{v['title']}\" ({v['views']:,} views) — {v['description'][:150]}"
            for v in videos[:5]
        ])

    prompt = f"""You are an expert direct-response ad strategist specialising in agencies that serve education businesses.

OFFER: {product}
PLATFORM: {platform}
AGENCY POSITIONING: Expert specialist agency helping education businesses (tutoring centres, training providers, online courses, preschools, coaching programmes) grow and scale.
TARGET AUDIENCE: Education business owners and leaders aged 30-55 — intelligent, experienced, sceptical of generic marketing promises.
{video_context}

Based on what works in this space, provide a strategic ad research brief:

1. TOP 3 WINNING ANGLES
For each angle: name it, explain why it works, give an example hook sentence.

2. EMOTIONAL TRIGGERS
List the 3-5 core emotional pain points and desires this audience has.

3. OBJECTIONS TO OVERCOME
Top 3 objections this audience has before buying/clicking.

4. MESSAGING FRAMEWORK
One-sentence value proposition that addresses the angle, pain, and objection together.

5. COMPETITOR GAPS
What are competitors NOT saying that creates an opportunity?

Format each section clearly. Be specific and tactical — no generic marketing advice."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "research": message.content[0].text,
        "videos_found": len(videos),
        "platform": platform,
    }

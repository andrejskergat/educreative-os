import os
import httpx
import anthropic


def _search_youtube(topic: str, api_key: str) -> list:
    base = "https://www.googleapis.com/youtube/v3"
    search_resp = httpx.get(f"{base}/search", params={
        "q": topic,
        "part": "snippet",
        "type": "video",
        "maxResults": 10,
        "order": "viewCount",
        "videoDuration": "short",
        "key": api_key,
    })
    search_resp.raise_for_status()
    items = search_resp.json().get("items", [])
    video_ids = [item["id"]["videoId"] for item in items]

    stats_resp = httpx.get(f"{base}/videos", params={
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": api_key,
    })
    stats_resp.raise_for_status()

    videos = []
    for item in stats_resp.json().get("items", []):
        videos.append({
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "views": int(item["statistics"].get("viewCount", 0)),
            "likes": int(item["statistics"].get("likeCount", 0)),
            "description": item["snippet"]["description"][:200],
            "url": f"https://youtube.com/watch?v={item['id']}",
        })

    videos.sort(key=lambda x: x["views"], reverse=True)
    return videos


def _research_with_claude(topic: str) -> dict:
    client = anthropic.Anthropic()

    prompt = f"""You are a content researcher for an expert agency helping education businesses get more students.

TOPIC: {topic}

Research this topic by drawing on what you know from:
1. Reddit communities: r/Entrepreneur, r/smallbusiness, r/teachingresources, r/onlineeducation, r/edtech, education Facebook groups
2. Common questions and complaints education business owners post online about this topic
3. What angles get the most engagement (comments, shares) when this topic is discussed in forums

Provide:

PAIN POINTS:
List 3-5 specific frustrations education business owners express about this topic online. Be specific — use the language they actually use.

TOP ANGLES:
List 3-5 content angles that consistently get high engagement on this topic. For each, note why it works (curiosity, fear, relief, social proof, etc.)

COMMON MISTAKES:
List 3 mistakes education business owners commonly make related to this topic, based on what you see discussed in forums and communities.

HOOK IDEAS:
Write 3 strong hook lines for a YouTube Short on this topic. Each must be a hard truth or surprising number — not a question.

Keep everything specific to education businesses (tutoring, preschools, enrichment centres, coaching, online courses)."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"forum_research": message.content[0].text}


def run(topic: str) -> dict:
    api_key = os.getenv("YOUTUBE_API_KEY")

    videos = []
    if api_key:
        try:
            videos = _search_youtube(topic, api_key)
        except Exception:
            pass

    forum_data = _research_with_claude(topic)

    return {
        "topic": topic,
        "videos": videos,
        "forum_research": forum_data["forum_research"],
    }

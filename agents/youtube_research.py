import os
import httpx


def run(topic: str) -> dict:
    api_key = os.getenv("YOUTUBE_API_KEY")
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
    return {"topic": topic, "videos": videos}

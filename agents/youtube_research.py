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


def _deep_research(topic: str) -> str:
    client = anthropic.Anthropic()

    prompt = f"""You are a senior content strategist researching what education business owners are actually saying online about this topic.

TOPIC: {topic}

Draw on everything you know from these specific communities and platforms:

REDDIT — search these subreddits: r/Entrepreneur, r/smallbusiness, r/tutoring, r/Teachers, r/edtech, r/onlineeducation, r/elearning, r/startups
QUORA — questions and answers from education business owners, tutors, school founders, enrichment centre owners
LINKEDIN — posts, comments and articles from education entrepreneurs, school owners, edtech founders, education consultants
FACEBOOK GROUPS — education business owner groups, tutoring business groups, preschool owner communities, private school groups
FORUMS & COMMUNITIES — TeacherForums, education entrepreneur podcasts, edtech communities, coaching business forums

For each section below, write specifically about what education businesses (tutoring centres, preschools, enrichment centres, coaching businesses, online course creators) post and discuss:

---

BURNING PAIN POINTS (from Reddit/Quora/Facebook groups):
List 5-6 specific frustrations education business owners vent about online. Use their exact language and phrasing — the way they actually write in posts and comments. Include which platform each is most common on.

---

TOP PERFORMING CONTENT ANGLES (from LinkedIn/YouTube/blogs):
List 5 content angles on this topic that get the most engagement (likes, comments, shares). For each: the angle, why it works emotionally (fear/relief/curiosity/social proof/status), and which platform it performs best on.

---

COMMON QUESTIONS (from Quora/Reddit):
List the 5 most upvoted or frequently asked questions education business owners ask about this topic. Write them exactly as people ask them.

---

MISTAKES & MISCONCEPTIONS (from community discussions):
List 4 mistakes or wrong beliefs education business owners commonly have about this topic, based on what you see corrected in forums and comment threads.

---

HOOK IDEAS FOR YOUTUBE SHORTS:
Write 5 strong opening hooks for a short video on this topic. Each must be:
- A hard truth, surprising number, or counterintuitive insight — NOT a question
- Written as something Andrej (15 years in education, helped 120+ education businesses in Singapore) would say from experience
- Specific to education businesses (not generic business advice)

---

BEST POSTING STRATEGY FOR THIS TOPIC:
One paragraph on which platform to lead with, what format works best, and the ideal CTA for this specific topic."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text


def run(topic: str) -> dict:
    api_key = os.getenv("YOUTUBE_API_KEY")

    videos = []
    if api_key:
        try:
            videos = _search_youtube(topic, api_key)
        except Exception:
            pass

    forum_research = _deep_research(topic)

    return {
        "topic": topic,
        "videos": videos,
        "forum_research": forum_research,
    }

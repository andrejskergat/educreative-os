import anthropic


def run(topic: str, youtube_data: dict) -> dict:
    client = anthropic.Anthropic()

    top_videos = youtube_data["videos"][:5]
    video_context = "\n".join([
        f"- \"{v['title']}\" ({v['views']:,} views) by {v['channel']}"
        for v in top_videos
    ])

    prompt = f"""You are an expert YouTube Shorts script writer. Your job is to write a high-performing YouTube Shorts script.

TOPIC: {topic}

TOP PERFORMING VIDEOS ON THIS TOPIC:
{video_context}

Write a YouTube Shorts script (60 seconds max, ~150 words) with this structure:
1. HOOK (first 3 seconds) - bold, pattern-interrupting opening line that stops the scroll
2. BODY (40 seconds) - 3-4 punchy points contrasting traditional education vs AI education
3. CTA (last 5 seconds) - clear call to action

Format your response as:
HOOK: [hook line]

BODY:
[body content with line breaks between points]

CTA: [call to action]

FULL SCRIPT:
[complete script as it would be read on camera]

Make it conversational, energetic, and specific. Use concrete examples and numbers where possible."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"script": message.content[0].text}

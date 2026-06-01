import anthropic


DEFAULT_CONTEXT = """You are creating content for an expert agency that helps education businesses grow and scale.
Audience: owners and leaders of education businesses — tutoring centres, training providers, online course creators, preschools, coaching programmes — aged 30-55.
Position the agency as the trusted expert partner. Voice: authoritative, warm, peer-to-peer. No hype.
Lead with the education business owner's real problem. Use concrete results and specifics.
Elevate the audience — treat them as intelligent professionals who have already tried the obvious solutions."""


def run(topic: str, youtube_data: dict, custom_context: str = "") -> dict:
    client = anthropic.Anthropic()

    top_videos = youtube_data["videos"][:5]
    video_context = "\n".join([
        f"- \"{v['title']}\" ({v['views']:,} views) by {v['channel']}"
        for v in top_videos
    ])

    context = custom_context.strip() or DEFAULT_CONTEXT

    prompt = f"""You are an expert YouTube Shorts script writer. Your job is to write a high-performing YouTube Shorts script.

AGENT INSTRUCTIONS:
{context}

TOPIC: {topic}

TOP PERFORMING VIDEOS ON THIS TOPIC:
{video_context}

Write a YouTube Shorts script (60 seconds max, ~150 words) with this structure:
1. HOOK (first 3 seconds) - a specific, pattern-interrupting insight that makes an education business owner stop scrolling
2. BODY (40 seconds) - 3-4 concrete points that demonstrate expert knowledge and genuine value for education businesses
3. CTA (last 5 seconds) - clear, low-pressure call to action that positions the agency as the expert guide

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

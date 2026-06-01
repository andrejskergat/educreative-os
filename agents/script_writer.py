import anthropic


DEFAULT_CONTEXT = """You are writing on behalf of an expert agency that helps education businesses grow.
Audience: founders and owners of education businesses — tutoring centres, online course creators, coaching businesses, training companies, edtech startups. Aged 28-50.
Brand voice: authoritative but direct. Speak like a trusted advisor who has seen what works and what doesn't. No hype, no fluff.
Position the agency as the expert guide — not the hero. The education business owner is the hero.
Use concrete numbers, real business outcomes, and industry-specific insight (enrolment rates, student LTV, course completion, acquisition cost).
Open with a provocative insight or uncomfortable truth that only an expert would say out loud.
Never use: 'game-changer', 'unlock', 'leverage', 'skyrocket', 'crushing it'."""


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
1. HOOK (first 3 seconds) - a sharp, expert insight or uncomfortable truth that stops the scroll. Must feel like it comes from someone who has worked with dozens of education businesses.
2. BODY (40 seconds) - 3-4 punchy, specific points that demonstrate deep expertise. Reference real business mechanics: pricing, retention, acquisition, positioning, operations.
3. CTA (last 5 seconds) - clear call to action that builds the agency's authority (e.g. follow for more, link in bio, comment with your situation)

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

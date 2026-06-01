import anthropic


def run(topic: str, script: str) -> dict:
    client = anthropic.Anthropic()

    prompt = f"""Write a YouTube Shorts description for an expert agency that helps education businesses grow.

TOPIC: {topic}
SCRIPT: {script[:500]}

Tone: authoritative, direct, no hype. Written for education business owners who want real insight, not motivation.
The agency is the expert guide — position it as a trusted advisor with deep education industry knowledge.

Provide:
1. DESCRIPTION: 2-3 sentences. Lead with the core insight or business outcome. Speak to education business owners specifically (tutoring, coaching, online courses, training). 150 chars max for mobile.
2. HASHTAGS: 8-10 hashtags mixing: education business niche tags, broader entrepreneurship tags, and 1-2 agency/marketing tags.

Format:
DESCRIPTION:
[description text]

HASHTAGS:
[hashtags]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"description": message.content[0].text}

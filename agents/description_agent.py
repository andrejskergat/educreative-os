import anthropic


def run(topic: str, script: str) -> dict:
    client = anthropic.Anthropic()

    prompt = f"""Write a YouTube Shorts description for this video.

TOPIC: {topic}
SCRIPT: {script[:500]}

Provide:
1. DESCRIPTION: 2-3 sentences, punchy, includes the main value proposition (150 chars max for mobile)
2. HASHTAGS: 8-10 relevant hashtags (mix of high-volume and niche)

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

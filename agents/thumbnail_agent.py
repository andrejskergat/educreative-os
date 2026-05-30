import anthropic


DEFAULT_CONTEXT = """Brand colours: dark navy (#0A0F2C) and electric cyan (#00D4FF).
Style: bold split-screen, high contrast, mobile-first.
No faces — use icons and symbols only. Always include a VS or contrast element."""


def run(topic: str, script: str, custom_context: str = "") -> dict:
    client = anthropic.Anthropic()

    context = custom_context.strip() or DEFAULT_CONTEXT

    prompt = f"""You are a YouTube thumbnail designer specialising in high-CTR (click-through rate) thumbnails for YouTube Shorts.

AGENT INSTRUCTIONS:
{context}

TOPIC: {topic}
SCRIPT HOOK: {script[:300]}

Design a thumbnail concept for this YouTube Short. Provide:

1. LAYOUT: Describe the visual composition (split screen, bold text placement, etc.)
2. MAIN TEXT: The large bold text that appears on the thumbnail (max 5 words)
3. SUBTEXT: Secondary text if any (max 4 words)
4. VISUAL ELEMENTS: What images/icons to use (no faces needed, use icons/symbols)
5. COLOUR SCHEME: Specific hex colours (high contrast, eye-catching)
6. EMOTION/TONE: What feeling the thumbnail should trigger (curiosity, shock, FOMO)
7. CANVA PROMPT: A ready-to-use prompt you could type into Canva's AI generator

Make it designed to maximise clicks on mobile. Think bold, simple, high contrast."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"thumbnail_concept": message.content[0].text}

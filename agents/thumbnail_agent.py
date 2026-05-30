import os
import re
import httpx
import anthropic


DEFAULT_CONTEXT = """Brand colours: dark navy (#0A0F2C) and electric cyan (#00D4FF).
Style: bold split-screen, high contrast, mobile-first.
No faces — use icons and symbols only. Always include a VS or contrast element."""


def _create_canva_thumbnail(canva_prompt: str) -> str | None:
    token = os.getenv("CANVA_API_TOKEN")
    if not token:
        return None
    try:
        resp = httpx.post(
            "https://api.canva.com/rest/v1/ai/generate-design",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"design_type": "youtube_thumbnail", "query": canva_prompt},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        designs = data.get("designs") or []
        if designs:
            did = designs[0].get("id")
            if did:
                return f"https://www.canva.com/design/{did}/edit"
    except Exception:
        pass
    return None


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

End your response with exactly this line:
CANVA PROMPT: [single sentence prompt for Canva AI]

Make it designed to maximise clicks on mobile. Think bold, simple, high contrast."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    concept_text = message.content[0].text

    canva_prompt_match = re.search(r"CANVA PROMPT:\s*(.+?)(?:\n|$)", concept_text, re.IGNORECASE)
    canva_prompt = canva_prompt_match.group(1).strip() if canva_prompt_match else f"YouTube thumbnail for: {topic}"

    canva_url = _create_canva_thumbnail(canva_prompt)

    result = {"thumbnail_concept": concept_text}
    if canva_url:
        result["canva_url"] = canva_url
    return result

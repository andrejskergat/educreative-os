import base64
import os
import anthropic
import httpx


DEFAULT_CONTEXT = """Brand colours: dark navy (#0A0F2C) and electric cyan (#00D4FF).
Style: bold split-screen, high contrast, mobile-first.
No faces — use icons and symbols only. Always include a VS or contrast element."""


def generate_image(prompt: str, job_id: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None

    image_prompt = (
        f"YouTube Shorts thumbnail, 9:16 vertical format, high contrast, bold text, "
        f"mobile-optimised design: {prompt}"
    )

    try:
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}",
            json={
                "instances": [{"prompt": image_prompt}],
                "parameters": {"sampleCount": 1, "aspectRatio": "9:16"},
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        img_bytes = base64.b64decode(b64)
        path = f"outputs/{job_id}_thumbnail.png"
        with open(path, "wb") as f:
            f.write(img_bytes)
        return f"/outputs/{job_id}_thumbnail.png"
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None


def run(topic: str, script: str, custom_context: str = "", job_id: str = "") -> dict:
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
7. IMAGE PROMPT: A single detailed sentence describing the image for an AI image generator (no markdown, plain text only)

Make it designed to maximise clicks on mobile. Think bold, simple, high contrast."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    concept = message.content[0].text

    # Extract the IMAGE PROMPT line and generate the actual image
    image_url = None
    if job_id:
        for line in concept.splitlines():
            if "IMAGE PROMPT:" in line:
                image_prompt = line.split("IMAGE PROMPT:", 1)[-1].strip()
                image_url = generate_image(image_prompt, job_id)
                break

    return {"thumbnail_concept": concept, "thumbnail_url": image_url}

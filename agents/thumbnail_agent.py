import base64
import os
import anthropic
import httpx


DEFAULT_CONTEXT = """Brand colours: dark navy (#0A0F2C) and electric cyan (#00D4FF).
Style: bold split-screen, high contrast, mobile-first.
No faces - use icons and symbols only. Always include a VS or contrast element."""


def generate_image(image_prompt: str, job_id: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found")
        return None

    full_prompt = (
        f"YouTube Shorts thumbnail, 9:16 vertical format, high contrast, "
        f"bold text, mobile-optimised design, no watermarks: {image_prompt}"
    )

    print(f"Generating image with Gemini for job {job_id}...")
    print(f"Prompt: {full_prompt[:100]}...")

    try:
        resp = httpx.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={api_key}",
            json={
                "instances": [{"prompt": full_prompt}],
                "parameters": {"sampleCount": 1, "aspectRatio": "9:16"},
            },
            timeout=60,
        )
        print(f"Gemini response status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Gemini error: {resp.text[:300]}")
            return None
        data = resp.json()
        b64 = data["predictions"][0]["bytesBase64Encoded"]
        img_bytes = base64.b64decode(b64)
        path = f"outputs/{job_id}_thumbnail.png"
        with open(path, "wb") as f:
            f.write(img_bytes)
        print(f"Image saved to {path}")
        return f"/outputs/{job_id}_thumbnail.png"
    except Exception as e:
        print(f"Image generation failed: {e}")
        return None


def run(topic: str, script: str, custom_context: str = "", job_id: str = "") -> dict:
    client = anthropic.Anthropic()
    context = custom_context.strip() or DEFAULT_CONTEXT

    prompt = f"""You are a YouTube thumbnail designer specialising in high-CTR thumbnails for YouTube Shorts.

AGENT INSTRUCTIONS:
{context}

TOPIC: {topic}
SCRIPT HOOK: {script[:300]}

Design a thumbnail concept and end your response with this exact section:

IMAGE PROMPT: [one plain sentence describing the thumbnail image for an AI image generator, no markdown, no emojis]

Before the IMAGE PROMPT, provide:
1. LAYOUT: Visual composition
2. MAIN TEXT: Bold text on thumbnail (max 5 words)
3. SUBTEXT: Secondary text (max 4 words)
4. VISUAL ELEMENTS: Icons and symbols to use
5. COLOUR SCHEME: Hex colours
6. EMOTION/TONE: Feeling to trigger"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    concept = message.content[0].text
    print(f"Thumbnail concept generated. Looking for IMAGE PROMPT...")

    # Extract IMAGE PROMPT line
    image_url = None
    image_prompt = None
    for line in concept.splitlines():
        if line.strip().startswith("IMAGE PROMPT:"):
            image_prompt = line.split("IMAGE PROMPT:", 1)[-1].strip()
            break

    if image_prompt:
        print(f"Found image prompt: {image_prompt[:80]}...")
        if job_id:
            image_url = generate_image(image_prompt, job_id)
    else:
        print("No IMAGE PROMPT found in concept output")
        print(f"Concept tail: {concept[-200:]}")

    return {"thumbnail_concept": concept, "thumbnail_url": image_url}

import os
import re
import httpx
import anthropic


DEFAULT_CONTEXT = """Brand colours: dark navy (#0A0F2C) and electric cyan (#00D4FF).
Style: bold, high-contrast, mobile-first. Clean and modern.
No stock photo faces — use bold typography, icons, and abstract visuals.
Always include a clear focal point and readable text at thumbnail size."""


def _create_canva_design(canva_prompt: str, design_type: str = "instagram_post") -> str | None:
    token = os.getenv("CANVA_API_TOKEN")
    if not token:
        return None
    try:
        resp = httpx.post(
            "https://api.canva.com/rest/v1/ai/generate-design",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"design_type": design_type, "query": canva_prompt},
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


def run(product: str, ad_copy: str, platform: str = "Meta", custom_context: str = "") -> dict:
    client = anthropic.Anthropic()

    context = custom_context.strip() or DEFAULT_CONTEXT

    prompt = f"""You are a performance creative director specialising in paid social ads.
Design ad creative concepts for 3 formats for this campaign.

PRODUCT/OFFER: {product}
PLATFORM: {platform}

BRAND CONTEXT:
{context}

AD COPY (use this to align visuals with messaging):
{ad_copy[:800]}

Design concepts for these 3 formats. For each:

FORMAT 1: Feed Post (1:1 square)
FORMAT 2: Story / Reel (9:16 vertical)
FORMAT 3: Banner / Headline (1.91:1 landscape)

For each format provide:
LAYOUT: Describe the visual composition in detail
HERO VISUAL: Main image/graphic element (be specific — what exactly do we see?)
TYPOGRAPHY: Headline text on the creative (max 6 words), font weight, placement
COLOUR USAGE: Which brand colours where, contrast rationale
MOTION SUGGESTION: If video/reel — describe 3-second hook animation
MOOD: One word that captures the feeling

End each format section with:
CANVA PROMPT: [single precise sentence for Canva AI to generate this]

Make each concept scroll-stopping on mobile. Think bold, simple, immediate."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    concept_text = message.content[0].text

    canva_prompts = re.findall(r"CANVA PROMPT:\s*(.+?)(?:\n|$)", concept_text, re.IGNORECASE)
    canva_url = None
    if canva_prompts:
        canva_url = _create_canva_design(canva_prompts[0].strip(), "instagram_post")

    result = {"creative_concepts": concept_text}
    if canva_url:
        result["canva_url"] = canva_url
    return result

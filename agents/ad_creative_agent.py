import os
import re
import httpx
import anthropic


DEFAULT_CONTEXT = """Brand colours: dark navy (#0A0F2C) and electric cyan (#00D4FF).
Style: premium, clean, high-contrast, mobile-first. This is an expert agency — the creative must signal quality and authority.
Avoid generic stock photos and clip art. Use bold typography, purposeful whitespace, and smart visual metaphors.
Every creative should feel like it was made by a specialist, not a template mill.
Target viewer: an education business owner who is intelligent, time-poor, and sceptical of marketing hype."""


def run(
    product: str,
    ad_copy: str,
    platform: str = "Meta",
    custom_context: str = "",
    competitor_analysis: str = "",
) -> dict:
    client = anthropic.Anthropic()

    context = custom_context.strip() or DEFAULT_CONTEXT

    competitor_section = (
        f"\nCOMPETITOR VISUAL PATTERNS (use to differentiate):\n{competitor_analysis[:800]}\n"
        if competitor_analysis.strip()
        else ""
    )

    prompt = f"""You are a performance creative director specialising in Meta (Facebook/Instagram) paid ads.
Design ad creative concepts for 3 formats optimised for Meta.

PRODUCT/OFFER: {product}
PLATFORM: {platform}

BRAND CONTEXT:
{context}
{competitor_section}
AD COPY (align visuals with this messaging):
{ad_copy[:1000]}

Design concepts for these 3 Meta ad formats:

FORMAT 1: Feed Post — 1:1 square (1080×1080px) — highest volume format
FORMAT 2: Story / Reel — 9:16 vertical (1080×1920px) — highest engagement
FORMAT 3: Feed Landscape — 1.91:1 (1200×628px) — desktop + right-column

For EACH format provide:
LAYOUT: Exact visual composition — where does each element sit?
HERO VISUAL: Specific image or graphic (describe precisely — not just "happy person", but e.g. "split screen: left = cluttered whiteboard, right = clean iPad interface")
HEADLINE ON CREATIVE: The 3-6 word text overlaid on the image (not the Meta headline field)
COLOUR: Which brand colours where, with contrast rationale
MOTION (for Reel/Story): Describe the 3-second opening animation
MOOD: Single word

End each format with:
CANVA PROMPT: [One precise, detailed sentence for Canva AI — include composition, colours, text, mood, format dimensions]

Make each concept immediately scroll-stopping on mobile. Bold over subtle. Simple over busy."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        messages=[{"role": "user", "content": prompt}],
    )

    concept_text = message.content[0].text
    canva_prompts = re.findall(r"CANVA PROMPT:\s*(.+?)(?:\n|$)", concept_text, re.IGNORECASE)

    return {
        "creative_concepts": concept_text,
        "canva_prompts": canva_prompts,
    }

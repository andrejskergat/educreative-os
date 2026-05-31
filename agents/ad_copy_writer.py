import anthropic


DEFAULT_CONTEXT = """Audience: Edtech agency founders and educators aged 28-45.
Voice: Direct, confident, results-focused. Use numbers and specifics.
Never use: 'game-changer', 'revolutionary', 'unlock your potential', or passive voice.
Always lead with the problem or a bold claim backed by evidence."""


def run(product: str, research: str, platform: str = "Meta", custom_context: str = "") -> dict:
    client = anthropic.Anthropic()

    context = custom_context.strip() or DEFAULT_CONTEXT

    prompt = f"""You are an elite direct-response copywriter. Write 3 high-converting ad copy variants for:

PRODUCT/OFFER: {product}
PLATFORM: {platform}

BRAND & AUDIENCE CONTEXT:
{context}

STRATEGIC RESEARCH:
{research[:1500]}

Write exactly 3 ad variants. Each variant targets a different angle from the research.
For each variant provide:

VARIANT [N] — [ANGLE NAME]
PRIMARY TEXT: (the main body copy, 100-150 words, opens with a hook, ends with soft CTA)
HEADLINE: (5-8 words, punchy, platform-optimized for {platform})
CTA BUTTON: (2-4 words)
FORMAT: (Feed / Story / Reel — recommend the best for this variant)

Rules:
- Variant 1: Lead with the biggest pain point
- Variant 2: Lead with a specific result or number
- Variant 3: Lead with a counter-intuitive claim or challenge

Make every word earn its place. No filler."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"ad_copy": message.content[0].text}

import anthropic


DEFAULT_CONTEXT = """Audience: Edtech agency founders and educators aged 28-45.
Voice: Direct, confident, results-focused. Use numbers and specifics.
Never use: 'game-changer', 'revolutionary', 'unlock your potential', or passive voice.
Always lead with the problem or a bold claim backed by evidence."""


def run(
    product: str,
    research: str,
    platform: str = "Meta",
    custom_context: str = "",
    angle: str = "",
    competitor_analysis: str = "",
) -> dict:
    client = anthropic.Anthropic()

    context = custom_context.strip() or DEFAULT_CONTEXT

    angle_section = f"\nSPECIFIC ANGLE TO USE:\n{angle.strip()}\n" if angle.strip() else ""

    competitor_section = (
        f"\nCOMPETITOR INTELLIGENCE (use this to differentiate, not copy):\n{competitor_analysis[:1200]}\n"
        if competitor_analysis.strip()
        else ""
    )

    prompt = f"""You are an elite direct-response copywriter specialising in Meta (Facebook/Instagram) ads for edtech.

PRODUCT/OFFER: {product}
PLATFORM: {platform}
{angle_section}
BRAND & AUDIENCE CONTEXT:
{context}

STRATEGIC RESEARCH:
{research[:800]}
{competitor_section}
Write exactly 3 high-converting Meta ad copy variants.
{"Each variant MUST use the specific angle provided above, expressed differently." if angle.strip() else "Each variant targets a different angle from the research."}

For each variant provide:

VARIANT [N] — [ANGLE NAME]
PRIMARY TEXT: (Facebook/Instagram body copy, 100-150 words, scroll-stopping first line, conversational, ends with a soft CTA)
HEADLINE: (5-7 words max — appears below the image in Meta feed)
LINK DESCRIPTION: (1 short sentence — appears as subheadline below headline, max 20 words)
CTA BUTTON: (choose from: Learn More / Sign Up / Get Quote / Send Message / Book Now / Download)
BEST FORMAT: (Feed Image / Feed Video / Story / Reel / Carousel)
AD TYPE: (Lead Form / WhatsApp / Link to Landing Page — recommend the best for this goal)

Rules:
- Variant 1: Lead with the biggest pain point the audience has right now
- Variant 2: Lead with a specific result, number, or social proof
- Variant 3: Lead with a counter-intuitive or pattern-interrupting claim

Make every word earn its place. Write like you're texting a smart friend, not writing an essay."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"ad_copy": message.content[0].text}

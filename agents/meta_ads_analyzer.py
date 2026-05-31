import anthropic


def _score_ad(ad: dict) -> float:
    """Score an ad based on signals of performance."""
    score = 0.0
    # Longevity is the strongest proxy — still-running ads are profitable
    score += min(ad.get("days_active", 0) / 7, 30)  # up to 30 pts for 7+ months
    if ad.get("still_active"):
        score += 10
    # Completeness of creative signals investment
    if ad.get("body"):
        score += 5
    if ad.get("headline"):
        score += 5
    if ad.get("description"):
        score += 3
    return score


def run(ads_data: dict, top_n: int = 10) -> dict:
    """Rank competitor ads and extract actionable creative intelligence."""
    ads = ads_data.get("ads", [])
    if not ads:
        return {
            "best_ads": [],
            "analysis": "No competitor ads found. Check that META_ACCESS_TOKEN is set and the niche keyword returns results.",
            "total_analyzed": 0,
        }

    scored = sorted(ads, key=_score_ad, reverse=True)
    best = scored[:top_n]

    client = anthropic.Anthropic()

    ads_summary = "\n\n".join([
        f"AD #{i+1} — {ad['page_name']} ({ad['days_active']} days active, {'still running' if ad['still_active'] else 'stopped'}) | Type: {ad['ad_type']}\n"
        f"BODY: {ad['body'][:300]}\n"
        f"HEADLINE: {ad['headline']}\n"
        f"DESCRIPTION: {ad['description'][:150]}"
        for i, ad in enumerate(best)
    ])

    niche = ads_data.get("niche", "this niche")

    prompt = f"""You are a Meta ads strategist. Analyze these top-performing competitor ads in the '{niche}' space and extract actionable creative intelligence.

These ads were ranked by longevity — the longer they've been running profitably, the higher the score.

TOP COMPETITOR ADS:
{ads_summary}

Provide a structured competitive analysis:

1. DOMINANT HOOKS (3-5)
What opening lines and hooks appear most frequently in winning ads? Quote examples.

2. WINNING HEADLINES
What patterns do the best headlines follow? List the top 3-5 with examples.

3. CTA PATTERNS
What CTAs and ad types (form, WhatsApp, link) dominate? What does this tell us?

4. EMOTIONAL ANGLES
What fears, desires, and pain points are competitors targeting most?

5. VISUAL PATTERNS
Based on descriptions/captions, what visual styles and formats are winning?

6. GAPS & OPPORTUNITIES
What angles are competitors NOT using that could stand out?

7. TOP 3 ADS TO EMULATE (not copy)
Pick the 3 strongest ads. For each: why it works + what to borrow from it.

Be specific. Quote the actual ad copy where relevant."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "best_ads": best,
        "analysis": message.content[0].text,
        "total_analyzed": len(ads),
        "total_shown": len(best),
    }

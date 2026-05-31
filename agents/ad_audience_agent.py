import anthropic


def run(product: str, research: str, platform: str = "Meta") -> dict:
    client = anthropic.Anthropic()

    prompt = f"""You are a paid media strategist expert in {platform} Ads audience targeting.

PRODUCT/OFFER: {product}
PLATFORM: {platform}

RESEARCH CONTEXT:
{research[:1200]}

Build a complete audience targeting brief:

1. CORE AUDIENCE (Primary)
- Age range & gender split
- Job titles / roles to target
- Key interests and behaviours ({platform}-specific)
- Income / education indicators if relevant

2. INTEREST-BASED AUDIENCES (3 segments)
For each: segment name, specific interests/pages to target, estimated size, why it works

3. LOOKALIKE STRATEGY
- Seed audience recommendation (what list/data to build from)
- Lookalike % tiers to test (1%, 3-5%, 10%)

4. EXCLUSIONS
- Who to exclude and why (prevent wasted spend)

5. RETARGETING LADDER
- Level 1: Warm (engaged with content)
- Level 2: Hot (visited site / watched 50%+ of video)
- Level 3: Hottest (add to cart / lead not converted)
- Suggested ad sequencing for each level

6. BUDGET SPLIT RECOMMENDATION
How to distribute initial test budget across audiences (in %)

7. TESTING PRIORITY
Which audience to test first and why — single sentence.

Be specific with {platform} targeting options. Use real interest categories and behaviour names."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"audience_brief": message.content[0].text}

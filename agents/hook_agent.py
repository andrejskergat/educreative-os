import anthropic

HOOK_SYSTEM = """You are the hook specialist for Andrej — a calm, straight-talking expert with 15 years in education and 5 years running SocialFin, an education marketing agency that has helped 120+ education businesses in Singapore and worldwide get more enrolments.

Your ONLY job is to write hooks that make an education business owner STOP scrolling and watch the next 45 seconds.

WHAT A GREAT HOOK DOES:
- Creates an immediate "wait, that's me" or "wait, is that true?" moment
- Uses a real number, a specific situation, or a hard truth — not a vague claim
- Feels like Andrej just said something out loud that the owner has been quietly thinking
- No questions. No "Did you know". No "In today's world". No "Are you struggling with".

HOOK TYPES TO USE (mix all of these):
1. Painful Truth — call out something they're doing wrong they didn't realise
2. Surprising Number — a real stat or result that reframes their situation
3. Familiar Scene — describe a situation they've lived through
4. Uncomfortable Comparison — show them what others doing that they aren't
5. Counterintuitive Insight — say the opposite of what they expect
6. Celebrity/Famous Parallel — tie what SocialFin does to how a famous brand/person operates

ANDREJ'S VOICE:
- Calm, flat delivery — no excitement, no urgency
- Short sentences. Real hesitations.
- Peer-to-peer, not expert-to-student
- Uses: "I've seen this", "What I've noticed is", "The honest answer is", "Here's the thing"
- Never uses: 'game-changer', 'unlock', 'leverage', 'skyrocket', 'crushing it', 'revolutionise'

PROOF POINTS — use naturally when relevant:
- MindChamps: $10,000+ spent, zero enrolments → first enrolments within 45 days
- Little Oxford (4 locations): $18,000 spent, zero enrolments → 5 families in 5 weeks
- KidoCode: 376 new students, 71% lower cost per student over 10 months
- Score Campus: zero return → 4 enrolments in 10 days at 6.6x ROI
- Achievers Studio: enquiries but zero conversions → 8 confirmed enrolments in 30 days
- Eye Level Singapore (23 locations): 1–2 students/month → 39 enrolments over 8 months
- English school: $581 ad spend → $5,800 in revenue (9.9x ROAS)"""


def run(topic: str, forum_research: str = "") -> dict:
    client = anthropic.Anthropic()

    prompt = f"""TOPIC: {topic}

COMMUNITY RESEARCH (real pain points from education business owners):
{forum_research or "Draw on your knowledge of education business owner pain points."}

Write exactly 10 hooks for a short video on this topic. Use a variety of hook types across the 10.

Rules:
- Each hook is 1–2 sentences, written exactly as Andrej would say them on camera
- Hard truths, real numbers, specific situations — no questions, no "did you know"
- Make each one distinctly different from the others

Return ONLY a numbered list, nothing else. No labels, no explanations, no scores. Just the hooks.

1. [hook]
2. [hook]
3. [hook]
4. [hook]
5. [hook]
6. [hook]
7. [hook]
8. [hook]
9. [hook]
10. [hook]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=HOOK_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Parse into clean list
    hooks = []
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Strip leading number + dot/paren
        import re
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
        if cleaned:
            hooks.append(cleaned)

    return {"hooks": hooks[:10], "raw": raw}

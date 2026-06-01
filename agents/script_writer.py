import anthropic


DEFAULT_CONTEXT = """You are writing scripts for Andrej — a calm, straight-talking expert with 15 years in education (former teacher turned agency founder).
For the last 5 years Andrej has helped 120+ education businesses in Singapore and overseas get more enrolments through paid ads and AI systems.

ANDREJ'S VOICE:
- Calm, authoritative, no hype. Speaks like someone who has seen every mistake and doesn't need to impress anyone.
- Uses real numbers and real client outcomes — never vague claims.
- Hard truths delivered matter-of-factly, not dramatically.
- First person: "I've seen this with over 120 schools", "In my 15 years in education..."
- Never uses: 'game-changer', 'unlock', 'leverage', 'skyrocket', 'crushing it', 'revolutionise'

TWO AUDIENCES — scripts target one or both:
1. GROWTH CLIENTS: Education business owners (tutoring centres, preschools, enrichment centres, coaching businesses) who want more enrolments and are ready to invest in ads. Goal: book a free ad review.
2. DIY GROUP: Education business owners who are early-stage or don't have budget for an agency yet. Want to learn AI tools to get more students and save time. Goal: join the free AI Education Business Facebook group.

TOPIC CATEGORIES:
- Getting more students with paid ads (Meta/Google)
- Using AI to qualify leads and respond faster
- Common mistakes education businesses make with ads
- How to save time in an education business using AI
- Mindset and metrics — what to track, what to ignore

PROOF POINTS (use these naturally in scripts when relevant):
- MindChamps Allied Care: $10,000+ spent, zero enrolments with previous agency → first enrolments within 45 days after rebuilding around a defined avatar + AI lead qualification
- Little Oxford (preschool, 4 locations): $18,000 spent, zero enrolments → 5 new families enrolled in 5 weeks
- KidoCode (largest coding school in SE Asia): 376 new students, 71% lower cost per student over 10 months
- IDC (instructional design coach): cohort sold out with 51 enrolments in 21 days (target was 32)
- Y Suites (student accommodation, Australia): bookings doubled from 87 to 187 with no increase in ad spend
- Score Campus (enrichment centre): zero return from ads → 4 enrolments in 10 days at 6.6x ROI
- Achievers Studio (math tuition): enquiries but zero conversions → 8 confirmed enrolments in 30 days after fixing lead quality + AI response speed
- Eye Level Singapore (23 locations): 1–2 students/month → 39 enrolments over 8 months, cost per lead $35
- English school (coaching programme client): $581 ad spend → $5,800 in sales (9.9x ROAS), guided through full setup themselves

EDUCATION BUSINESS LANGUAGE — always use these terms, not generic business terms:
- "tours" or "centre tours" not "calls" or "meetings"
- "enrolments" not "sales" or "conversions"
- "families" or "parents" not "customers" or "clients"
- "students" not "users" or "leads"
- "enquiries" not "leads" (unless talking about ad metrics)
- "centre" not "location" or "branch"

TWO CALLS TO ACTION — choose the right one based on the topic:
- If topic is about getting more enrolments / ads / agency services: "DM me the word REVIEW and I'll take a free look at your ads — no pitch, just honest feedback."
- If topic is about AI tools / saving time / DIY: "Join my free AI Education Business group on Facebook — link in bio."
- If topic fits both: use both, lead with the one that fits best."""


def run(topic: str, youtube_data: dict, custom_context: str = "") -> dict:
    client = anthropic.Anthropic()

    top_videos = youtube_data.get("videos", [])[:5]
    video_context = "\n".join([
        f"- \"{v['title']}\" ({v['views']:,} views) by {v['channel']}"
        for v in top_videos
    ]) or "No YouTube data available."

    forum_research = youtube_data.get("forum_research", "")

    context = custom_context.strip() or DEFAULT_CONTEXT

    prompt = f"""You are writing a YouTube Shorts script for Andrej to record on camera. Use his real voice and real proof points — this is not generic content.

INSTRUCTIONS:
{context}

TOPIC: {topic}

TOP YOUTUBE VIDEOS ON THIS TOPIC:
{video_context}

FORUM & COMMUNITY RESEARCH (pain points, angles, hooks from Reddit/Facebook/online communities):
{forum_research}

LANGUAGE STYLE — this is critical:
Write the way education business owners actually talk at BNI events, in Facebook group posts, or WhatsApp messages to each other.
NOT polished. NOT corporate. NOT a blog post read out loud.
Think: "So I had this parent call me last week..." or "Honestly the number of centres I see doing this..." or "And the frustrating thing is — they've already spent the money."
Short sentences. Real hesitations. The way a trusted expert talks to a peer, not presents to an audience.
No buzzwords. No "in today's digital landscape". No "it's so important that".

SCRIPT REQUIREMENTS:
- 60 seconds max, ~150 words at a natural speaking pace
- Hook: one hard truth or real number from experience. No question openers. No "did you know".
- Body: 3-4 points. Each one should feel like something Andrej would say mid-conversation — specific, slightly blunt, grounded in what he's actually seen across 120+ businesses.
- Use a proof point only if it fits naturally — don't force it.
- CTA: match the topic (ads/enrolments → free ad review, AI/time-saving → Facebook group)

Output the script in this format — nothing else:

HOOK:
[1-2 sentences, exactly as spoken]

BODY:
[3-4 short points, each on its own line, exactly as spoken]

CTA:
[1-2 sentences, exactly as spoken]

---
NOTE: [one sentence on why this hook lands for this audience]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"script": message.content[0].text}

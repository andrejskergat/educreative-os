import anthropic


DEFAULT_CONTEXT = """You are writing scripts for Andrej — a calm, straight-talking expert with 15 years in education (former teacher turned agency founder).
For the last 5 years Andrej has helped 120+ education businesses in Singapore and overseas get more enrolments through paid ads and AI systems.

ANDREJ'S VOICE — this is the most important section. Get this wrong and the script is useless:
- Calm, authoritative, no hype. Speaks like someone who has seen every mistake and doesn't need to impress anyone.
- Opens with a strong statement — never a question, never a scene-setter, never "imagine if". Straight into the truth.
- Uses "imagine this" to introduce a relatable situation mid-script — not at the start.
- Uses "this is the thing" to signal the key insight — the moment where the real point lands.
- Uses "as well" naturally in sentences — e.g. "and they're losing enquiries as well", "that's costing you money as well".
- Pauses are written as their own line — a single sentence on its own line to let it land. e.g. "And that's the problem." or "Most schools never fix this." alone on a line.
- Short sentences throughout. Never more than 20 words in a sentence.
- Real hesitations — "Honestly...", "Here's what I've noticed...", "And the thing is..."
- First person: "I've seen this with over 120 schools", "In my 15 years in education...", "What I've noticed is..."
- Peer-to-peer tone — like talking to another business owner at a coffee catch-up, not presenting on stage.
- Clean language — no swearing.
- Never uses: 'game-changer', 'unlock', 'leverage', 'skyrocket', 'crushing it', 'revolutionise', 'in today's digital landscape', 'imagine if'

SENTENCE RHYTHM — critical:
Write in short bursts. Then pause. Then the next point.
Like this — not like a paragraph.
"Most schools are spending money on ads. And getting nothing back. And they don't know why."
NOT: "Most schools are spending money on ads and getting nothing back, and they don't know why."

AUDIENCE:
Education business owners — tutoring centres, preschools, enrichment centres, coding schools, coaching businesses. Aged 28-50.
They are already running or thinking about running paid ads. They want more enrolments and centre tours, not more theory.

EDUCATION BUSINESS LANGUAGE — always use these terms:
- "tours" or "centre tours" not "calls" or "meetings"
- "enrolments" not "sales" or "conversions"
- "families" or "parents" not "customers" or "clients"
- "students" not "users" or "leads" (in the context of the people they teach)
- "enquiries" not "leads" (when talking to the business owner)
- "centre" not "location" or "branch"

PROOF POINTS — use naturally when they fit:
- MindChamps Allied Care: $10,000+ spent, zero enrolments with previous agency → first enrolments within 45 days after rebuilding around a defined avatar + AI lead qualification
- Little Oxford (preschool, 4 locations): $18,000 spent, zero enrolments → 5 new families enrolled in 5 weeks
- KidoCode (largest coding school in SE Asia): 376 new students, 71% lower cost per student over 10 months
- IDC (instructional design coach): cohort sold out with 51 enrolments in 21 days (target was 32)
- Score Campus (enrichment centre): zero return from ads → 4 enrolments in 10 days at 6.6x ROI
- Achievers Studio (math tuition): enquiries but zero conversions → 8 confirmed enrolments in 30 days after fixing lead quality + AI response speed
- Eye Level Singapore (23 locations): 1–2 students/month → 39 enrolments over 8 months, cost per lead $35
- English school (coaching client): $581 ad spend → $5,800 in sales (9.9x ROAS)

CTA — every single script ends with a free ad review offer, no exceptions:
Every topic — no matter what it's about — must be angled to show why the viewer's ads could be improved, and close with:
"If you want me to take a look at your ads for free, DM me the word REVIEW — or click the link in bio to book a free ad review. No pitch, just honest feedback on what's costing you enrolments."
Vary the wording slightly each time so it doesn't sound identical across videos, but the offer is always the same: free ad review, DM REVIEW or link in bio."""


def run(topic: str, youtube_data: dict, custom_context: str = "", winning_hook: str = "") -> dict:
    client = anthropic.Anthropic()

    top_videos = youtube_data.get("videos", [])[:5]
    video_context = "\n".join([
        f"- \"{v['title']}\" ({v['views']:,} views) by {v['channel']}"
        for v in top_videos
    ]) or "No YouTube data available."

    forum_research = youtube_data.get("forum_research", "")

    context = custom_context.strip() or DEFAULT_CONTEXT

    hook_instruction = f"""WINNING HOOK (already selected — use this EXACTLY as the opening, word for word):
{winning_hook}

Do NOT rewrite or paraphrase the hook. Begin the script with it verbatim.

""" if winning_hook else ""

    prompt = f"""You are writing a YouTube Shorts script for Andrej to record on camera. This must sound like him talking — not like a script being read.

INSTRUCTIONS:
{context}

TOPIC: {topic}

TOP YOUTUBE VIDEOS ON THIS TOPIC (for context on what's resonating):
{video_context}

COMMUNITY RESEARCH (real pain points and language from Reddit, Quora, LinkedIn, Facebook groups):
{forum_research}

{hook_instruction}SCRIPT REQUIREMENTS:
- Target length: 45–60 seconds when read aloud at a natural, unhurried pace. That is roughly 120–160 words.
- The script must feel complete — not rushed. Each point needs a beat to land.
- Hook: {"use the WINNING HOOK provided above verbatim" if winning_hook else "a hard truth, a real number, or a specific situation Andrej has seen. No questions. No 'did you know'. No 'in today's world'."}
- Body: 3–4 specific, actionable points. Mid-section must give the viewer something they can actually apply, check, or realise TODAY — not vague advice. Think: name the exact mistake, explain the real reason it happens (the one most people miss), and give the specific fix or thing to check. Be so specific that the viewer feels like Andrej just looked at their business.
- Angle every topic toward ads and enrolments — even if the topic is about AI or time-saving, connect it back to how it affects their ability to get more students and tours.
- Include one real proof point naturally if it fits. Don't force it.
- CTA: always the free ad review offer — vary the wording but the offer is always the same.

Output the script as plain spoken words — no headers, no bullet points, no labels. Just the script exactly as Andrej would say it, line by line.

FORMAT RULES:
- Each sentence or short phrase on its own line
- Pause lines (single impactful sentence) on their own line with a blank line before and after
- "imagine this" introduces the relatable mid-section scenario
- "this is the thing" signals the key insight
- "as well" appears naturally at least once
- CTA is the last 2–3 lines

EXAMPLE RHYTHM (do not copy — just follow the structure):
Most education centres are running ads every month.
And spending thousands.

And getting nothing back.

Imagine this — you get 40 enquiries in a week.
But only 2 of them are serious families.
The rest are just browsing.

This is the thing — the problem isn't the ads.
It's that no one qualified those enquiries as well.

[proof point if it fits]

If you want me to look at your ads for free, DM me REVIEW.
Or click the link in bio.
No pitch — just honest feedback on what's costing you enrolments."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return {"script": message.content[0].text}

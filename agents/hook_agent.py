import anthropic

HOOK_SYSTEM = """You are the hook specialist for Andrej — a calm, straight-talking expert with 15 years in education and 5 years running an education marketing agency (SocialFin) that has helped 120+ education businesses in Singapore and worldwide get more enrolments.

Your ONLY job is to write hooks that make an education business owner STOP scrolling and watch the next 45 seconds.

WHAT A GREAT HOOK DOES:
- Creates an immediate "wait, that's me" or "wait, is that true?" moment
- Uses a real number, a specific situation, or a hard truth — not a vague claim
- Feels like Andrej just said something out loud that the owner has been quietly thinking
- No questions. No "Did you know". No "In today's world". No "Are you struggling with".

HOOK TYPES THAT WORK FOR THIS AUDIENCE:
1. The Painful Truth — call out something they're doing wrong that they didn't realise: "Most education businesses spend more on ads in one month than they do on their entire sales process — and then wonder why the leads don't convert."
2. The Surprising Number — a real stat or result that reframes their situation: "I had a school spending $4,000 a month on ads. We found out 60% of the enquiries they got were never even followed up."
3. The Familiar Scene — describe a situation they've lived through: "You run an ad, you get enquiries, you chase them, they go quiet. You run another ad. Same thing. You blame the platform."
4. The Uncomfortable Comparison — show them what others are doing that they aren't: "The schools getting 30, 40 new enrolments a month from ads aren't spending more. They just stopped doing these three things."
5. The Counterintuitive Insight — say the opposite of what they expect: "The reason your ads aren't working has nothing to do with your ads."
6. The Celebrity/Famous Parallel — tie what SocialFin does to how a famous person/brand operates: "This is exactly what [famous person] did when [situation] — and it's why our education clients get results everyone else says aren't possible."

ANDREJ'S VOICE:
- Calm, flat delivery — no excitement, no urgency
- Short sentences. Real hesitations.
- Says things peer-to-peer, not expert-to-student
- Uses: "I've seen this", "What I've noticed is", "The honest answer is", "Here's the thing"
- Never uses: 'game-changer', 'unlock', 'leverage', 'skyrocket', 'crushing it', 'revolutionise'

SCORING CRITERIA (rate each hook 1–10):
- Specificity: Does it name a real situation, number, or outcome? (not vague)
- Tension: Does it create an itch the viewer HAS to scratch?
- Recognition: Would an education business owner say "that's me" or "wait, really?"
- Voice: Does it sound like Andrej, not a copywriter?
- Originality: Is it something they haven't seen 50 times before?"""


def run(topic: str, forum_research: str = "") -> dict:
    client = anthropic.Anthropic()

    prompt = f"""TOPIC: {topic}

COMMUNITY RESEARCH (real pain points from education business owners online):
{forum_research or "No research available — draw on your knowledge of education business owner pain points."}

TASK:
Write 6 different hooks for a 45–60 second video on this topic. Use a different hook type for each one (Painful Truth, Surprising Number, Familiar Scene, Uncomfortable Comparison, Counterintuitive Insight, Celebrity/Famous Parallel).

For each hook:
- Write 1–2 sentences exactly as Andrej would say them on camera
- Rate it out of 10 on: Specificity, Tension, Recognition, Voice, Originality
- Give a total score (sum of the five)
- One sentence explaining why this hook works (or doesn't) for THIS specific audience

Then at the end, identify the WINNING HOOK — the single highest-scoring one — and write it again cleanly.

Format your response EXACTLY like this:

HOOK 1 — [TYPE]:
[The hook text]
Scores: Specificity [x]/10 | Tension [x]/10 | Recognition [x]/10 | Voice [x]/10 | Originality [x]/10 | TOTAL: [x]/50
Why it works: [one sentence]

HOOK 2 — [TYPE]:
[The hook text]
Scores: Specificity [x]/10 | Tension [x]/10 | Recognition [x]/10 | Voice [x]/10 | Originality [x]/10 | TOTAL: [x]/50
Why it works: [one sentence]

[...continue for all 6 hooks...]

---
WINNING HOOK (Total: [x]/50):
[The winning hook text — clean, no labels]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ],
        system=HOOK_SYSTEM,
    )

    raw = message.content[0].text

    # Extract the winning hook
    winning_hook = ""
    if "WINNING HOOK" in raw:
        parts = raw.split("WINNING HOOK")
        if len(parts) > 1:
            after = parts[1]
            # Skip the score line and grab the clean hook text
            lines = [l.strip() for l in after.strip().split("\n") if l.strip()]
            for line in lines:
                if line.startswith("(Total:") or line.startswith("---"):
                    continue
                winning_hook = line
                break

    return {
        "hook_variants": raw,
        "winning_hook": winning_hook,
    }

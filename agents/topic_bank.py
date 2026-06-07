"""
Daily topic rotation bank for SocialFin education business scripts.
Topics are grouped by theme and cycle through day-of-year to avoid repeats.
"""
from datetime import date

TOPICS = [
    # ── SOCIAL vs ADS ──────────────────────────────────────────────────────────
    "Why posting on social media won't fill your education centre — and what actually will",
    "The difference between social media and paid ads for education businesses (and why most get it backwards)",
    "Your Instagram followers aren't turning into enrolments — here's the real reason",
    "Stop trying to go viral. Here's what fills education centres instead.",
    "Why 10,000 followers means nothing if your enquiry inbox is empty",

    # ── ADS THAT ACTUALLY BRING STUDENTS ───────────────────────────────────────
    "The education centre ad that actually brought students (and why yours probably isn't doing this)",
    "Why most education ads get clicks but zero enrolments — and the one thing that fixes it",
    "What a $581 ad spend that returned $5,800 looks like — and why it worked",
    "The 3 things your ad needs before you spend another dollar on Meta",
    "Why your education ad looks exactly like every other education ad (and what to do instead)",
    "The biggest mistake education businesses make with their ad creative",
    "Why changing your ad budget won't fix your enrolment problem",
    "The silent killer of education ads: what happens after the click",
    "Why beautiful ads for education businesses don't get enrolments",
    "From zero enrolments to 5 families in 5 weeks — what changed in the ads",

    # ── AI FOR EDUCATION BUSINESSES ────────────────────────────────────────────
    "How to get more students 3x faster using AI (and it's not a chatbot)",
    "3 ways education businesses are using AI to get more enrolments right now",
    "The AI tool I use to follow up education enquiries in under 5 minutes — and why it triples conversions",
    "Why the school getting 39 enrolments a month uses AI, and you don't (yet)",
    "How AI pre-qualifies education leads before you spend a minute on the phone",
    "The AI workflow that turned 8 stuck enquiries into 8 confirmed enrolments in 30 days",
    "Why slow follow-up is killing your education enrolments — and how AI fixes it",
    "AI for education marketing: what actually works vs. what's just hype",
    "How to use AI to identify which parents are ready to enrol right now",

    # ── LEAD QUALITY & CONVERSION ──────────────────────────────────────────────
    "Why you're getting enquiries but no enrolments — and it's not the parents' fault",
    "The education centre lead quality problem nobody talks about",
    "Why chasing enquiries that go cold is costing you more than the ads themselves",
    "The difference between an enquiry and a qualified family — and why it matters",
    "How to stop wasting time on bad enquiries and only talk to families ready to enrol",
    "What a 6.6x ROI from education ads actually looks like",
    "The conversion fix that turned 0 enrolments into 4 in 10 days",

    # ── MARKETING STRATEGY FOR EDUCATION ──────────────────────────────────────
    "Why your education marketing strategy is built for the wrong parent",
    "The education business avatar mistake that wastes every dollar you spend on ads",
    "Why 'more leads' is the wrong goal for your education centre",
    "The 3 marketing metrics every education business owner should actually track",
    "How to build an education marketing system that runs without you",
    "Why your education centre's best month was a fluke — and how to make it repeatable",
    "The education marketing audit that reveals why ads stop working after month 2",

    # ── AGENCY vs DIY vs WRONG AGENCY ─────────────────────────────────────────
    "Why $10,000 in education ads and zero enrolments isn't the platform's fault",
    "What most marketing agencies won't tell education business owners",
    "The difference between an agency that runs education ads and one that gets enrolments",
    "Why we turn down education businesses that aren't ready for paid ads",
    "The 5 questions to ask any marketing agency before you sign with them (if you run an education business)",
    "What happened when MindChamps switched to a marketing system built for education",
    "Why 120+ education businesses chose a specialist over a generalist agency",

    # ── CELEBRITY/FAMOUS PARALLEL ──────────────────────────────────────────────
    "What Apple's marketing teaches education businesses about why parents choose you (it's not price)",
    "The Warren Buffett principle that the best education marketing agencies all follow",
    "How the top-ranked education businesses market themselves — and why it's the opposite of what you think",
    "What Netflix can teach your education centre about keeping parents engaged until they book a tour",
    "The Amazon approach to education marketing: why the best schools play the long game",

    # ── TOURS & ENROLMENTS ────────────────────────────────────────────────────
    "Why more centre tours don't automatically mean more enrolments",
    "The tour booking system that fills your calendar without you chasing anyone",
    "Why parents visit your centre and never come back — and how to fix it before they walk out",
    "How to get 10 centre tours a week without doubling your ad spend",
    "The pre-tour follow-up that converts 40% more families before they even visit",

    # ── PRESCHOOL / ENRICHMENT / TUITION SPECIFIC ─────────────────────────────
    "Why preschool ads are different from every other education ad — and most agencies don't know it",
    "The enrichment centre marketing mistake that lets your competitor take families you already warmed up",
    "Why tuition centres are the hardest education business to market — and the one strategy that works",
    "How coding schools are getting 376 new students a year through paid ads (and what you can steal from it)",
]


def get_topic_for_today() -> str:
    """Return today's topic using day-of-year index."""
    day_index = date.today().timetuple().tm_yday - 1  # 0-based
    return TOPICS[day_index % len(TOPICS)]


def get_topic_for_date(target_date: date) -> str:
    day_index = target_date.timetuple().tm_yday - 1
    return TOPICS[day_index % len(TOPICS)]


def get_all_topics() -> list:
    return list(TOPICS)

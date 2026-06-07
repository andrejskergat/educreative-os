"""
Standalone daily script generator — runs in GitHub Actions.
Picks today's topic, runs the full pipeline (research → hooks → script),
and writes the output to scripts/YYYY-MM-DD.md
"""
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from agents.topic_bank import get_topic_for_today
from agents import youtube_research, hook_agent, script_writer


def main():
    topic = get_topic_for_today()
    today = date.today().isoformat()

    print(f"[1/3] Topic: {topic}")
    yt_data = youtube_research.run(topic)
    video_count = len(yt_data.get("videos", []))
    print(f"      Research done — {video_count} YouTube videos + community insights")

    print("[2/3] Generating hooks...")
    hook_data = hook_agent.run(topic, yt_data.get("forum_research", ""))
    winning_hook = hook_data["winning_hook"]
    print(f"      Winning hook: {winning_hook[:80]}...")

    print("[3/3] Writing script...")
    script_data = script_writer.run(topic, yt_data, winning_hook=winning_hook)
    script = script_data["script"]
    print("      Script written.")

    output_dir = Path("scripts")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{today}.md"

    content = f"""# Daily Script — {today}

**Topic:** {topic}

---

## Winning Hook

> {winning_hook}

---

## Full Script

{script}

---

## All Hook Variants

{hook_data['hook_variants']}

---

## Community Research

{yt_data.get('forum_research', '')}
"""

    output_path.write_text(content, encoding="utf-8")
    print(f"\nSaved to {output_path}")

    # Write topic to GitHub Actions output if available
    github_output = os.getenv("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"topic={topic}\n")
            f.write(f"file={output_path}\n")


if __name__ == "__main__":
    main()

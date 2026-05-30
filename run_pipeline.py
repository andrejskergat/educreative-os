import sys
import os
from dotenv import load_dotenv

load_dotenv()

from agents import youtube_research, script_writer, thumbnail_agent, description_agent


def run(topic: str):
    print(f"\n{'='*60}")
    print(f"  EDUCREATIVE AI PIPELINE")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    print("[1/4] Running YouTube Research Agent...")
    yt_data = youtube_research.run(topic)
    print(f"  Found {len(yt_data['videos'])} videos\n")

    print("  Top 5 videos on this topic:")
    for i, v in enumerate(yt_data["videos"][:5], 1):
        print(f"  {i}. {v['title'][:60]}")
        print(f"     {v['views']:,} views - {v['channel']}")
        print(f"     {v['url']}")
    print()

    print("[2/4] Running Script Writer Agent...")
    script_data = script_writer.run(topic, yt_data)
    print()
    print("-" * 60)
    print("  SCRIPT")
    print("-" * 60)
    print(script_data["script"])
    print()

    print("[3/4] Running Thumbnail Agent...")
    thumb_data = thumbnail_agent.run(topic, script_data["script"])
    print()
    print("-" * 60)
    print("  THUMBNAIL CONCEPT")
    print("-" * 60)
    print(thumb_data["thumbnail_concept"])
    print()

    print("[4/4] Running Description Agent...")
    desc_data = description_agent.run(topic, script_data["script"])
    print()
    print("-" * 60)
    print("  DESCRIPTION & HASHTAGS")
    print("-" * 60)
    print(desc_data["description"])
    print()

    print("="*60)
    print("  PIPELINE COMPLETE")
    print("="*60)


if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "traditional education vs AI education business"
    run(topic)

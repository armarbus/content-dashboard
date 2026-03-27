# processor/main.py
"""
Entry point for the weekly scrape pipeline.
Run by GitHub Actions every Monday at 05:00 UTC.

Usage:
    python -m processor.main
"""
import os
from datetime import date, datetime, timezone
from dotenv import load_dotenv

from processor.apify_client import fetch_all_accounts, fetch_hashtag_reels, DISCOVERY_HASHTAGS
from processor.viral_score import calculate_viral_score, get_week_start_date
from processor.ai_analyzer import analyze_reel
from processor.db_client import upsert_reel, get_avg_views_for_handle, upsert_summary, get_top_reels_for_week
from processor.summary_generator import generate_weekly_summary
from processor.transcriber import transcribe_top_reels, TOP_N_TRANSCRIBE

load_dotenv()


def _build_record(reel: dict, week_start_str: str) -> dict:
    """Score + analyze a single reel and return the complete record dict."""
    handle = reel["competitor_handle"]

    posted_at = reel.get("posted_at")
    if posted_at:
        try:
            posted_dt = datetime.fromisoformat(str(posted_at).replace("Z", "+00:00"))
            days_since = max(0, (datetime.now(timezone.utc) - posted_dt).days)
        except Exception:
            days_since = 7
    else:
        days_since = 7

    avg_views = get_avg_views_for_handle(handle)
    score = calculate_viral_score(
        views=reel.get("views", 0),
        likes=reel.get("likes", 0),
        comments=reel.get("comments", 0),
        days_since_posted=days_since,
        avg_views_for_handle=avg_views,
    )
    analysis = analyze_reel(caption=reel.get("caption", ""), handle=handle)

    return {
        **reel,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "week_start_date": week_start_str,
        "viral_score": score,
        "hook": analysis["hook"],
        "hook_type": analysis["hook_type"],
        "theme": analysis["theme"],
        "ai_why": analysis["ai_why"],
        "ai_your_version": analysis["ai_your_version"],
        "source": reel.get("source", "account"),
        "niche_tag": reel.get("niche_tag"),
        "transcript": None,
    }


def run():
    today = date.today()
    week_start = get_week_start_date(today)
    week_start_str = week_start.isoformat()
    print(f"🚀 Starting weekly scrape for week of {week_start_str}")

    # Pass 1 — Collect + Score + Analyze account reels (no upsert yet)
    print("\n📷 Fetching reels from Apify...")
    raw_reels = fetch_all_accounts(max_per_account=10)
    print(f"  → {len(raw_reels)} total reels fetched")

    print("\n🧠 Analyzing reels with OpenAI...")
    all_records = []
    for i, reel in enumerate(raw_reels, 1):
        print(f"  [{i}/{len(raw_reels)}] @{reel['competitor_handle']} — {reel['reel_id']}")
        record = _build_record(reel, week_start_str)
        all_records.append(record)

    # Pass 2 — Transcribe top 20
    print(f"\n🎙️  Transcribing top {TOP_N_TRANSCRIBE} reels with Whisper...")
    transcripts = transcribe_top_reels(all_records, top_n=TOP_N_TRANSCRIBE)
    for record in all_records:
        record["transcript"] = transcripts.get(record["reel_id"])
    print(f"  → {len(transcripts)} reels transcribed")

    # Pass 3 — Upsert all account reels
    for record in all_records:
        upsert_reel(record)
    print(f"\n✅ {len(all_records)} reels saved to Supabase")

    # Pass 4 — Hashtag discovery
    for hashtag in DISCOVERY_HASHTAGS:
        print(f"\n🔍 Fetching hashtag reels for #{hashtag}...")
        hashtag_reels = fetch_hashtag_reels(hashtag, max_results=20)
        print(f"  → {len(hashtag_reels)} reels fetched")
        for reel in hashtag_reels:
            record = _build_record(reel, week_start_str)
            upsert_reel(record)
        print(f"  → #{hashtag} reels saved")

    # Pass 5 — Weekly summary
    print("\n📋 Generating weekly summary...")
    top_reels = get_top_reels_for_week(week_start_str)
    summary = generate_weekly_summary(top_reels, week_start_str)
    upsert_summary(summary)
    print("  → Weekly summary saved")

    print(f"\n🎉 Pipeline complete for week of {week_start_str}")


if __name__ == "__main__":
    run()

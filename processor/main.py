# processor/main.py
"""
Entry point for the weekly scrape pipeline.
Run by GitHub Actions every Monday at 06:00.

Usage:
    python -m processor.main
"""
import os
from datetime import date, datetime, timezone
from dotenv import load_dotenv

from processor.apify_client import fetch_all_accounts
from processor.viral_score import calculate_viral_score, get_week_start_date
from processor.ai_analyzer import analyze_reel
from processor.db_client import upsert_reel, get_avg_views_for_handle, upsert_summary, get_top_reels_for_week
from processor.summary_generator import generate_weekly_summary

load_dotenv()


def run():
    today = date.today()
    week_start = get_week_start_date(today)
    week_start_str = week_start.isoformat()
    print(f"🚀 Starting weekly scrape for week of {week_start_str}")

    # Step 1: Fetch all reels from Apify
    print("\n📷 Fetching reels from Apify...")
    raw_reels = fetch_all_accounts(max_per_account=10)
    print(f"  → {len(raw_reels)} total reels fetched")

    # Step 2: Process each reel
    print("\n🧠 Analyzing reels with OpenAI...")
    for i, reel in enumerate(raw_reels, 1):
        handle = reel["competitor_handle"]
        print(f"  [{i}/{len(raw_reels)}] @{handle} — {reel['reel_id']}")

        # Calculate days since posted
        posted_at = reel.get("posted_at")
        if posted_at:
            try:
                posted_dt = datetime.fromisoformat(str(posted_at).replace("Z", "+00:00"))
                days_since = (datetime.now(timezone.utc) - posted_dt).days
            except Exception:
                days_since = 7
        else:
            days_since = 7

        # Get account average for relative scoring
        avg_views = get_avg_views_for_handle(handle)

        # Calculate viral score
        score = calculate_viral_score(
            views=reel.get("views", 0),
            likes=reel.get("likes", 0),
            comments=reel.get("comments", 0),
            days_since_posted=days_since,
            avg_views_for_handle=avg_views,
        )

        # AI analysis
        analysis = analyze_reel(
            caption=reel.get("caption", ""),
            handle=handle,
        )

        # Compose final record
        record = {
            **reel,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "week_start_date": week_start_str,
            "viral_score": score,
            "hook": analysis["hook"],
            "hook_type": analysis["hook_type"],
            "theme": analysis["theme"],
            "ai_why": analysis["ai_why"],
            "ai_your_version": analysis["ai_your_version"],
        }

        upsert_reel(record)

    print(f"\n✅ {len(raw_reels)} reels saved to Supabase")

    # Step 3: Generate weekly summary
    print("\n📋 Generating weekly summary...")
    top_reels = get_top_reels_for_week(week_start_str)
    summary = generate_weekly_summary(top_reels, week_start_str)
    upsert_summary(summary)
    print("  → Weekly summary saved")

    print(f"\n🎉 Pipeline complete for week of {week_start_str}")


if __name__ == "__main__":
    run()

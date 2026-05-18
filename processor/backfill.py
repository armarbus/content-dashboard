# processor/backfill.py
"""
Eenmalige backfill: haalt ~2 maanden reels op voor alle accounts.
Filtert competitor reels onder 20k views — geen research waarde.
Eigen accounts worden altijd opgeslagen.

Draai via GitHub Actions → workflow_dispatch (één keer).
"""
import os
from datetime import date, datetime, timezone
from dotenv import load_dotenv

from processor.apify_client import ACCOUNTS, fetch_reels_for_account, parse_reel
from processor.viral_score import calculate_viral_score, get_week_start_date
from processor.ai_analyzer import analyze_reel
from processor.db_client import upsert_reel, get_avg_views_for_handle
from processor.transcriber import transcribe_top_reels

load_dotenv()

MIN_COMPETITOR_VIEWS = 20_000
REELS_PER_ACCOUNT = 50  # ~2 maanden bij 5-6 reels/week


def _week_for_reel(posted_at, today: date) -> tuple[str, int]:
    """Bepaalt week_start_date en days_since op basis van posted_at."""
    if posted_at:
        try:
            dt = datetime.fromisoformat(str(posted_at).replace("Z", "+00:00"))
            week_str = get_week_start_date(dt.date()).isoformat()
            days_since = max(0, (datetime.now(timezone.utc) - dt).days)
            return week_str, days_since
        except Exception:
            pass
    return get_week_start_date(today).isoformat(), 7


def run():
    today = date.today()
    print(f"🚀 Backfill gestart — {today}")
    print(f"   Filter: concurrenten ≥ {MIN_COMPETITOR_VIEWS:,} views | eigen accounts altijd")
    print(f"   Reels per account: {REELS_PER_ACCOUNT}\n")

    all_records = []
    total_skipped = 0

    for account in ACCOUNTS:
        handle = account["handle"]
        is_own = account["is_own"]

        print(f"📷 @{handle} ({'eigen' if is_own else 'concurrent'}) — ophalen...")
        raw_items = fetch_reels_for_account(handle, max_results=REELS_PER_ACCOUNT)

        account_kept = 0
        account_skipped = 0

        for raw in raw_items:
            parsed = parse_reel(raw, handle, is_own)
            if not parsed or not parsed["reel_id"]:
                continue

            views = parsed.get("views", 0)
            if not is_own and views < MIN_COMPETITOR_VIEWS:
                account_skipped += 1
                total_skipped += 1
                continue

            week_str, days_since = _week_for_reel(parsed.get("posted_at"), today)
            avg_views = get_avg_views_for_handle(handle)

            score = calculate_viral_score(
                views=views,
                likes=parsed.get("likes", 0),
                comments=parsed.get("comments", 0),
                days_since_posted=days_since,
                avg_views_for_handle=avg_views,
            )
            analysis = analyze_reel(caption=parsed.get("caption", ""), handle=handle)

            all_records.append({
                **parsed,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "week_start_date": week_str,
                "viral_score": score,
                "hook": analysis["hook"],
                "hook_type": analysis["hook_type"],
                "theme": analysis["theme"],
                "content_type": analysis["content_type"],
                "ai_why": analysis["ai_why"],
                "ai_your_version": analysis["ai_your_version"],
                "source": "account",
                "niche_tag": None,
                "transcript": None,
            })
            account_kept += 1

        print(f"   → {account_kept} opgeslagen, {account_skipped} overgeslagen (< {MIN_COMPETITOR_VIEWS:,} views)")

    print(f"\n🎙️  Transcriberen ({len(all_records)} reels)...")
    transcripts = transcribe_top_reels(all_records)
    for record in all_records:
        record["transcript"] = transcripts.get(record["reel_id"])
    print(f"   → {len(transcripts)} getranscribed")

    print(f"\n💾 Opslaan in Supabase...")
    for record in all_records:
        upsert_reel(record)

    print(f"\n✅ Backfill klaar!")
    print(f"   Opgeslagen:   {len(all_records)} reels")
    print(f"   Overgeslagen: {total_skipped} reels (onder {MIN_COMPETITOR_VIEWS:,} views)")
    print(f"   Getranscribed: {len(transcripts)} reels")


if __name__ == "__main__":
    run()

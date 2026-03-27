# processor/db_client.py
"""
Supabase read/write operations for the processor.
Uses service_role key — never used in the Streamlit frontend.
"""
import os
from supabase import create_client, Client


_client: Client = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_KEY"],
        )
    return _client


VALID_HOOK_TYPES = {'identiteit', 'tegenstelling', 'discipline', 'transformatie', 'lifestyle', 'anders'}
VALID_THEMES = {'hybrid', 'kracht', 'voeding', 'mindset', 'lifestyle', 'anders'}


def upsert_reel(reel: dict) -> None:
    """Inserts or updates a reel record using reel_id as the conflict key."""
    reel = dict(reel)
    if reel.get("hook_type") not in VALID_HOOK_TYPES:
        reel["hook_type"] = "anders"
    if reel.get("theme") not in VALID_THEMES:
        reel["theme"] = "anders"
    client = get_client()
    client.table("reels").upsert(reel, on_conflict="reel_id").execute()


def get_avg_views_for_handle(handle: str, limit: int = 20) -> float:
    """
    Returns the average views of the last `limit` reels for this handle.
    Used for relative viral score calculation.
    Returns 0.0 if no data exists yet (cold start).
    """
    client = get_client()
    response = (
        client.table("reels")
        .select("views")
        .eq("competitor_handle", handle)
        .order("posted_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = response.data
    if not rows:
        return 0.0
    return sum(r["views"] for r in rows) / len(rows)


def upsert_summary(summary: dict) -> None:
    """Inserts or updates a weekly summary record."""
    client = get_client()
    client.table("summaries").upsert(summary, on_conflict="week_start_date").execute()


def get_top_reels_for_week(week_start_date: str, limit: int = 20) -> list:
    """Fetches top reels for a given week, sorted by viral_score desc. Used for summary generation."""
    client = get_client()
    response = (
        client.table("reels")
        .select("hook,hook_type,theme,views,viral_score,competitor_handle,ai_why")
        .eq("week_start_date", week_start_date)
        .eq("is_own_account", False)
        .order("viral_score", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data

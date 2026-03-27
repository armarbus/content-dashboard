# processor/apify_client.py
"""
Fetches the latest Instagram Reels for a given account via Apify.
Uses the apify/instagram-scraper actor configured for Reels only.
"""
import os
from apify_client import ApifyClient


ACTOR_ID = "apify/instagram-scraper"

ACCOUNTS = [
    {"handle": "williamdurnik",  "is_own": False},
    {"handle": "chrismouton_",   "is_own": False},
    {"handle": "harleysshields", "is_own": False},
    {"handle": "kvnramirezz",    "is_own": False},
    {"handle": "alexmegino",     "is_own": False},
    {"handle": "kirstyhendey",   "is_own": False},
    {"handle": "aymanraoul",     "is_own": True},
]


def fetch_reels_for_account(handle: str, max_results: int = 10) -> list[dict]:
    """
    Fetches up to max_results recent Reels for the given Instagram handle.
    Returns a list of raw Apify result dicts.
    """
    client = ApifyClient(os.environ["APIFY_API_TOKEN"])

    run_input = {
        "directUrls": [f"https://www.instagram.com/{handle}/reels/"],
        "resultsType": "posts",
        "resultsLimit": max_results,
        "addParentData": False,
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items


def parse_reel(raw: dict, handle: str, is_own: bool) -> dict:
    """
    Normalises a raw Apify item into a clean dict matching the DB schema.
    Returns None if the item is not a video/reel.
    """
    if not raw.get("isVideo", True):
        return None

    return {
        "reel_id":           raw.get("shortCode") or raw.get("id", ""),
        "is_own_account":    is_own,
        "competitor_handle": handle,
        "video_url":         raw.get("url") or f"https://www.instagram.com/reel/{raw.get('shortCode', '')}/",
        "thumbnail_url":     raw.get("displayUrl", ""),
        "caption":           raw.get("caption", "") or "",
        "views":             max(0, raw.get("videoViewCount") or raw.get("videoPlayCount") or 0),
        "likes":             max(0, raw.get("likesCount") or 0),
        "comments":          max(0, raw.get("commentsCount") or 0),
        "posted_at":         raw.get("timestamp"),
    }


def fetch_all_accounts(max_per_account: int = 10) -> list[dict]:
    """Fetches and parses reels for all accounts. Returns flat list of parsed dicts."""
    results = []
    for account in ACCOUNTS:
        print(f"Fetching reels for @{account['handle']}...")
        raw_items = fetch_reels_for_account(account["handle"], max_per_account)
        for raw in raw_items:
            parsed = parse_reel(raw, account["handle"], account["is_own"])
            if parsed and parsed["reel_id"]:
                results.append(parsed)
        print(f"  → {len(raw_items)} items fetched")
    return results

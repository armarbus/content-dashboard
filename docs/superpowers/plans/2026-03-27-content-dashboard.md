# Content Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated Instagram Reels research dashboard that scrapes 7 accounts weekly, scores virality with AI analysis, and displays results in a 6-tab Streamlit app.

**Architecture:** A Python processor (run weekly via GitHub Actions) scrapes Instagram Reels via Apify, calculates viral scores, sends each reel to OpenAI for hook/theme/AI analysis, and upserts results into Supabase. A Streamlit dashboard reads from Supabase and renders 6 tabs for competitor research, hook discovery, and own-performance tracking.

**Tech Stack:** Python 3.11, Streamlit, Supabase (PostgreSQL), Apify Python client, OpenAI GPT-4o-mini, GitHub Actions, `python-dotenv`, `pandas`, `plotly`

---

## File Structure

```
content-research/
├── .github/
│   └── workflows/
│       └── weekly_scrape.yml       # Cron job: runs processor every Monday 06:00
├── processor/
│   ├── apify_client.py             # Fetch reels from Apify per account
│   ├── viral_score.py              # Viral score formula
│   ├── ai_analyzer.py              # OpenAI: hook, theme, ai_why, ai_your_version
│   ├── db_client.py                # Supabase upsert + avg_views query
│   ├── summary_generator.py        # OpenAI: generate weekly summary
│   └── main.py                     # Orchestrator: runs full pipeline
├── dashboard/
│   ├── app.py                      # Streamlit entry point, tab routing
│   ├── queries.py                  # All read queries from Supabase
│   └── tabs/
│       ├── viral_overview.py       # Tab 1: top 10 viral this week
│       ├── competitor_breakdown.py # Tab 2: per-account view
│       ├── hook_library.py         # Tab 3: hooks grouped by type
│       ├── value_content.py        # Tab 4: content by theme
│       ├── my_performance.py       # Tab 5: @aymanraoul performance
│       └── weekly_summary.py       # Tab 6: AI weekly summary
├── supabase/
│   └── schema.sql                  # Full DB schema + RLS policies
├── tests/
│   ├── test_viral_score.py
│   └── test_ai_analyzer.py
├── .env.example
├── requirements.txt
└── .streamlit/
    └── secrets.toml.example        # Template for Streamlit Cloud secrets
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `.streamlit/secrets.toml.example`

- [ ] **Step 1: Create requirements.txt**

```
apify-client==1.8.1
openai==1.30.1
supabase==2.4.6
streamlit==1.35.0
pandas==2.2.2
plotly==5.22.0
python-dotenv==1.0.1
```

- [ ] **Step 2: Create .env.example**

```bash
# Copy this to .env and fill in your values
APIFY_API_TOKEN=your_apify_token_here
OPENAI_API_KEY=your_openai_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
SUPABASE_ANON_KEY=your_anon_key_here
```

- [ ] **Step 3: Create .gitignore**

```
.env
__pycache__/
*.pyc
.DS_Store
.streamlit/secrets.toml
venv/
.venv/
```

- [ ] **Step 4: Create .streamlit/secrets.toml.example**

```toml
# Copy to .streamlit/secrets.toml for local dev, or add to Streamlit Cloud secrets
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key_here"
```

- [ ] **Step 5: Create virtual environment and install dependencies**

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 6: Commit**

```bash
git init
git add requirements.txt .env.example .gitignore .streamlit/secrets.toml.example
git commit -m "feat: initial project setup"
```

---

## Task 2: Database Schema

**Files:**
- Create: `supabase/schema.sql`

- [ ] **Step 1: Create schema.sql**

```sql
-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Reels table
create table if not exists reels (
  reel_id            text primary key,
  is_own_account     boolean not null default false,
  scraped_at         timestamptz not null default now(),
  competitor_handle  text not null,
  video_url          text,
  thumbnail_url      text,
  caption            text,
  hook               text,
  hook_type          text check (hook_type in ('identiteit','tegenstelling','discipline','transformatie','lifestyle','anders')),
  theme              text check (theme in ('hybrid','kracht','voeding','mindset','lifestyle','anders')),
  views              integer default 0,
  likes              integer default 0,
  comments           integer default 0,
  posted_at          timestamptz,
  viral_score        integer check (viral_score >= 0 and viral_score <= 100),
  ai_why             text,
  ai_your_version    text,
  week_start_date    date not null
);

-- Summaries table
create table if not exists summaries (
  week_start_date  date primary key,
  generated_at     timestamptz not null default now(),
  trending_themes  text,
  best_hook_types  text,
  top3_to_copy     text,
  weekly_advice    text
);

-- Indexes for common queries
create index if not exists idx_reels_week on reels(week_start_date);
create index if not exists idx_reels_handle on reels(competitor_handle);
create index if not exists idx_reels_score on reels(viral_score desc);
create index if not exists idx_reels_own on reels(is_own_account);

-- Enable Row Level Security
alter table reels enable row level security;
alter table summaries enable row level security;

-- Allow anon (Streamlit dashboard) to read only
create policy "anon read reels" on reels
  for select to anon using (true);

create policy "anon read summaries" on summaries
  for select to anon using (true);

-- Allow service_role (GitHub Actions processor) full access (default: already has it)
```

- [ ] **Step 2: Run schema in Supabase**

Go to your Supabase project → SQL Editor → paste the contents of `supabase/schema.sql` → click Run.

Expected: Tables `reels` and `summaries` appear in the Table Editor. No errors.

- [ ] **Step 3: Commit**

```bash
git add supabase/schema.sql
git commit -m "feat: add database schema with RLS"
```

---

## Task 3: Viral Score Module

**Files:**
- Create: `processor/viral_score.py`
- Create: `tests/test_viral_score.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_viral_score.py
from processor.viral_score import calculate_viral_score, get_week_start_date
from datetime import date, timedelta

def test_score_above_average_is_high():
    # A video with 2x the average views should score ~70 from view component
    score = calculate_viral_score(
        views=20000, likes=500, comments=50,
        days_since_posted=3, avg_views_for_handle=10000
    )
    assert score >= 60

def test_score_below_average_is_low():
    score = calculate_viral_score(
        views=2000, likes=50, comments=5,
        days_since_posted=10, avg_views_for_handle=10000
    )
    assert score < 30

def test_score_capped_at_100():
    score = calculate_viral_score(
        views=1000000, likes=100000, comments=10000,
        days_since_posted=0, avg_views_for_handle=1000
    )
    assert score == 100

def test_score_never_negative():
    score = calculate_viral_score(
        views=0, likes=0, comments=0,
        days_since_posted=30, avg_views_for_handle=10000
    )
    assert score >= 0

def test_cold_start_no_zero_division():
    # avg_views_for_handle=0 should not crash
    score = calculate_viral_score(
        views=5000, likes=100, comments=20,
        days_since_posted=2, avg_views_for_handle=0
    )
    assert 0 <= score <= 100

def test_week_start_date_is_monday():
    # Any date should return the Monday of that week
    thursday = date(2026, 3, 26)
    monday = get_week_start_date(thursday)
    assert monday == date(2026, 3, 23)
    assert monday.weekday() == 0  # 0 = Monday
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "/Users/Ayman/Desktop/Claude code/Content research"
source venv/bin/activate
python -m pytest tests/test_viral_score.py -v
```

Expected: `ModuleNotFoundError` — `processor.viral_score` does not exist yet.

- [ ] **Step 3: Create processor/__init__.py**

```python
# processor/__init__.py
# (empty file — marks processor as a Python package)
```

- [ ] **Step 4: Implement viral_score.py**

```python
# processor/viral_score.py
from datetime import date, timedelta


def calculate_viral_score(
    views: int,
    likes: int,
    comments: int,
    days_since_posted: float,
    avg_views_for_handle: float,
) -> int:
    """
    Returns a 0-100 score relative to the account's own average views.
    A video with 2x avg views scores ~70 from the view component alone.
    """
    # View component: relative to account average (max 70 pts)
    view_ratio = views / max(avg_views_for_handle, 1)
    view_score = min(70, view_ratio * 35)

    # Engagement rate component (max 20 pts)
    engagement = (likes + comments * 2) / max(views, 1)
    engagement_score = min(20, engagement * 200)

    # Recency bonus: full points within 14 days, zero after (max 10 pts)
    recency = max(0.0, 1.0 - (days_since_posted / 14))
    recency_score = recency * 10

    return min(100, int(view_score + engagement_score + recency_score))


def get_week_start_date(reference_date: date) -> date:
    """Returns the Monday of the week containing reference_date."""
    return reference_date - timedelta(days=reference_date.weekday())
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_viral_score.py -v
```

Expected: All 6 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add processor/__init__.py processor/viral_score.py tests/test_viral_score.py
git commit -m "feat: viral score calculation with relative scoring"
```

---

## Task 4: Apify Client

**Files:**
- Create: `processor/apify_client.py`

- [ ] **Step 1: Create apify_client.py**

```python
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
        "views":             raw.get("videoViewCount") or raw.get("videoPlayCount") or 0,
        "likes":             raw.get("likesCount") or 0,
        "comments":          raw.get("commentsCount") or 0,
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
```

- [ ] **Step 2: Verify import works (no API call yet)**

```bash
python -c "from processor.apify_client import ACCOUNTS, parse_reel; print('OK', len(ACCOUNTS), 'accounts')"
```

Expected: `OK 7 accounts`

- [ ] **Step 3: Commit**

```bash
git add processor/apify_client.py
git commit -m "feat: apify client for instagram reels scraping"
```

---

## Task 5: AI Analyzer

**Files:**
- Create: `processor/ai_analyzer.py`
- Create: `tests/test_ai_analyzer.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ai_analyzer.py
from processor.ai_analyzer import build_prompt_content, parse_ai_response, extract_hook_text

def test_extract_hook_text_from_caption():
    caption = "Stop met alleen bulken. Bouw een hybrid physique. #fitness #hybrid"
    hook = extract_hook_text(caption)
    assert hook.startswith("Stop met alleen bulken")
    assert "#" not in hook

def test_extract_hook_text_from_hashtag_caption():
    caption = "#fitness #hybrid stop met bulken"
    hook = extract_hook_text(caption)
    # Should skip leading hashtags
    assert hook == ""  # Falls back to AI

def test_extract_hook_text_empty():
    assert extract_hook_text("") == ""
    assert extract_hook_text(None) == ""

def test_parse_ai_response_valid():
    raw = '{"hook": "Stop met bulken", "hook_type": "tegenstelling", "theme": "hybrid", "ai_why": "Werkt goed.", "ai_your_version": "Jouw versie hier."}'
    result = parse_ai_response(raw)
    assert result["hook"] == "Stop met bulken"
    assert result["hook_type"] == "tegenstelling"
    assert result["theme"] == "hybrid"

def test_parse_ai_response_invalid_json():
    result = parse_ai_response("niet geldig json {{{")
    assert result["hook"] == "Geen tekst beschikbaar"
    assert result["hook_type"] == "anders"

def test_build_prompt_has_brand_context():
    content = build_prompt_content(caption="Test caption", handle="williamdurnik")
    assert "hybrid" in content.lower()
    assert "williamdurnik" in content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_ai_analyzer.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Implement ai_analyzer.py**

```python
# processor/ai_analyzer.py
"""
Sends each reel's metadata to OpenAI GPT-4o-mini for hook/theme/AI analysis.
"""
import os
import json
import re
from openai import OpenAI


SYSTEM_PROMPT = """Je bent een content analist voor Ayman, een hybrid performance coach.
Zijn merk: kracht + hardlopen, discipline, stoïcijnse mindset, masculine lifestyle.
Doelgroep: mannen 16-35 die sterker, droger en mentaal scherper willen worden.
Merkboodschap: "Bouw een hybride lichaam. Bouw discipline. Bouw jezelf."
Zijn eigen hook-stijl: identiteit ("mannen die trainen winnen"), tegenstelling
("stop met alleen bulken"), discipline ("je hoeft je niet goed te voelen om te winnen"),
lifestyle ("sober living, early mornings, consistent training").

Analyseer de aangeleverde Instagram Reel en geef ALLEEN een JSON object terug (geen markdown):
{
  "hook": "eerste 6-8 woorden van de tekst, of korte beschrijving als er geen tekst is",
  "hook_type": "een van: identiteit | tegenstelling | discipline | transformatie | lifestyle | anders",
  "theme": "een van: hybrid | kracht | voeding | mindset | lifestyle | anders",
  "ai_why": "1-2 zinnen waarom deze video viral gaat in de hybrid/fitness niche",
  "ai_your_version": "concrete hook of idee hoe Ayman dit kan nabouwen voor zijn merk"
}"""

FALLBACK = {
    "hook": "Geen tekst beschikbaar",
    "hook_type": "anders",
    "theme": "anders",
    "ai_why": "",
    "ai_your_version": "",
}


def extract_hook_text(caption: str | None) -> str:
    """
    Extracts the first meaningful 6-8 words from a caption.
    Returns empty string if caption starts with hashtag/emoji or is empty.
    """
    if not caption:
        return ""
    stripped = caption.strip()
    if not stripped or stripped[0] in ("#", "@") or not stripped[0].isalpha():
        return ""
    # Take first ~8 words
    words = stripped.split()[:8]
    return " ".join(words)


def build_prompt_content(caption: str, handle: str) -> str:
    hook_hint = extract_hook_text(caption)
    return f"""Account: @{handle}
Caption: {caption or "(geen caption beschikbaar)"}
Mogelijke hook (eerste woorden): {hook_hint or "(niet extraheerbaar, genereer zelf)"}

Geef je JSON analyse:"""


def parse_ai_response(raw: str) -> dict:
    """Parses OpenAI response string into dict. Returns fallback on any error."""
    try:
        # Strip markdown code blocks if present
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(cleaned)
        # Validate required keys
        for key in ("hook", "hook_type", "theme", "ai_why", "ai_your_version"):
            if key not in data:
                data[key] = FALLBACK[key]
        return data
    except Exception:
        return FALLBACK.copy()


def analyze_reel(caption: str, handle: str) -> dict:
    """
    Calls OpenAI with reel metadata and returns parsed analysis dict.
    Falls back gracefully on API errors.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt_content(caption, handle)},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        raw = response.choices[0].message.content
        return parse_ai_response(raw)
    except Exception as e:
        print(f"  ⚠️  OpenAI error for @{handle}: {e}")
        return FALLBACK.copy()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_ai_analyzer.py -v
```

Expected: All 6 tests PASS (no API calls made).

- [ ] **Step 5: Commit**

```bash
git add processor/ai_analyzer.py tests/test_ai_analyzer.py
git commit -m "feat: openai hook/theme analyzer with fallback handling"
```

---

## Task 6: Database Client

**Files:**
- Create: `processor/db_client.py`

- [ ] **Step 1: Create db_client.py**

```python
# processor/db_client.py
"""
Supabase read/write operations for the processor.
Uses service_role key — never used in the Streamlit frontend.
"""
import os
from supabase import create_client, Client


def get_client() -> Client:
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_KEY"],
    )


def upsert_reel(reel: dict) -> None:
    """Inserts or updates a reel record using reel_id as the conflict key."""
    client = get_client()
    client.table("reels").upsert(reel, on_conflict="reel_id").execute()


def get_avg_views_for_handle(handle: str, limit: int = 20) -> float:
    """
    Returns the average views of the last `limit` reels for this handle.
    Used for relative viral score calculation.
    Returns 0.0 if no data exists yet (cold start — handled in viral_score.py).
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


def get_top_reels_for_week(week_start_date: str, limit: int = 20) -> list[dict]:
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
```

- [ ] **Step 2: Verify import works**

```bash
python -c "from processor.db_client import upsert_reel, get_avg_views_for_handle; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add processor/db_client.py
git commit -m "feat: supabase db client with upsert and avg-views query"
```

---

## Task 7: Weekly Summary Generator

**Files:**
- Create: `processor/summary_generator.py`

- [ ] **Step 1: Create summary_generator.py**

```python
# processor/summary_generator.py
"""
Generates a weekly summary using OpenAI based on the top reels of the week.
"""
import os
import json
from openai import OpenAI


SUMMARY_SYSTEM_PROMPT = """Je bent een content strateeg voor Ayman, een hybrid performance coach.
Zijn doelgroep: mannen 16-35. Merk: hybrid training, discipline, masculinity, lifestyle.
Analyseer de top Instagram Reels van deze week van zijn concurrenten en geef een wekelijkse samenvatting
als JSON met exact deze keys: trending_themes, best_hook_types, top3_to_copy, weekly_advice.
Schrijf in het Nederlands. Wees direct en praktisch — Ayman post 3 Shorts per dag."""

FALLBACK_SUMMARY = {
    "trending_themes": "Geen data beschikbaar voor deze week.",
    "best_hook_types": "",
    "top3_to_copy": "",
    "weekly_advice": "",
}


def generate_weekly_summary(top_reels: list[dict], week_start_date: str) -> dict:
    """
    Takes a list of top reels and generates a weekly summary dict.
    Returns a dict ready for upsert into the summaries table.
    """
    if not top_reels:
        return {"week_start_date": week_start_date, **FALLBACK_SUMMARY}

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    reels_text = "\n".join([
        f"- Hook: '{r.get('hook', '')}' | Type: {r.get('hook_type', '')} | "
        f"Thema: {r.get('theme', '')} | Score: {r.get('viral_score', 0)} | "
        f"Account: @{r.get('competitor_handle', '')} | Waarom: {r.get('ai_why', '')}"
        for r in top_reels[:15]
    ])

    user_prompt = f"""Week van {week_start_date}. Top Reels van concurrenten:

{reels_text}

Geef een JSON samenvatting met:
- trending_themes: 2-3 zinnen over welke thema's domineren
- best_hook_types: welke hook-types het best werkten en waarom
- top3_to_copy: top 3 concrete video-ideeën voor Ayman om na te maken (met hook-suggestie)
- weekly_advice: 1 aanbeveling voor Aymanʼs content strategie deze week"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        raw = response.choices[0].message.content
        # Strip markdown if present
        import re
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(cleaned)
        return {"week_start_date": week_start_date, **data}
    except Exception as e:
        print(f"  ⚠️  Summary generation error: {e}")
        return {"week_start_date": week_start_date, **FALLBACK_SUMMARY}
```

- [ ] **Step 2: Verify import**

```bash
python -c "from processor.summary_generator import generate_weekly_summary; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add processor/summary_generator.py
git commit -m "feat: weekly summary generator via openai"
```

---

## Task 8: Main Processor Orchestrator

**Files:**
- Create: `processor/main.py`

- [ ] **Step 1: Create main.py**

```python
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
```

- [ ] **Step 2: Test dry run (no API calls, just import check)**

```bash
python -c "from processor.main import run; print('Import OK')"
```

Expected: `Import OK`

- [ ] **Step 3: Commit**

```bash
git add processor/main.py
git commit -m "feat: main processor orchestrator"
```

---

## Task 9: GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/weekly_scrape.yml`

- [ ] **Step 1: Create weekly_scrape.yml**

```yaml
# .github/workflows/weekly_scrape.yml
name: Weekly Content Scrape

on:
  schedule:
    - cron: '0 6 * * 1'  # Every Monday at 06:00 UTC
  workflow_dispatch:       # Allow manual trigger from GitHub UI

jobs:
  scrape:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run weekly scrape
        env:
          APIFY_API_TOKEN: ${{ secrets.APIFY_API_TOKEN }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: python -m processor.main
```

- [ ] **Step 2: Add repository secrets in GitHub**

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret.

Add these 4 secrets:
- `APIFY_API_TOKEN` — from apify.com → Settings → Integrations → API tokens
- `OPENAI_API_KEY` — from platform.openai.com → API keys
- `SUPABASE_URL` — from Supabase project → Settings → API → Project URL
- `SUPABASE_SERVICE_KEY` — from Supabase project → Settings → API → service_role key

- [ ] **Step 3: Commit and push to GitHub**

```bash
git add .github/workflows/weekly_scrape.yml
git commit -m "feat: github actions weekly scrape cron"
git push -u origin main
```

- [ ] **Step 4: Trigger manual run to verify**

Go to GitHub → Actions tab → "Weekly Content Scrape" → "Run workflow" → Run.

Expected: Green checkmark within ~15 minutes. Check Supabase Table Editor to confirm rows were inserted into `reels`.

---

## Task 10: Dashboard — Core Setup + Tab 1 (Viral Overview)

**Files:**
- Create: `dashboard/__init__.py`
- Create: `dashboard/queries.py`
- Create: `dashboard/tabs/__init__.py`
- Create: `dashboard/tabs/viral_overview.py`
- Create: `dashboard/app.py`

- [ ] **Step 1: Create dashboard/queries.py**

```python
# dashboard/queries.py
"""All read-only Supabase queries used by the Streamlit dashboard."""
import os
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"],
    )


@st.cache_data(ttl=300)
def get_available_weeks() -> list[str]:
    """Returns list of week_start_dates available in DB, newest first."""
    response = get_client().table("reels").select("week_start_date").execute()
    weeks = sorted(set(r["week_start_date"] for r in response.data), reverse=True)
    return weeks


@st.cache_data(ttl=300)
def get_reels(
    week: str | None = None,
    min_score: int = 0,
    handles: list[str] | None = None,
    hook_types: list[str] | None = None,
    themes: list[str] | None = None,
    own_only: bool = False,
    competitors_only: bool = False,
) -> list[dict]:
    q = get_client().table("reels").select("*")
    if week:
        q = q.eq("week_start_date", week)
    if min_score > 0:
        q = q.gte("viral_score", min_score)
    if own_only:
        q = q.eq("is_own_account", True)
    if competitors_only:
        q = q.eq("is_own_account", False)
    if handles:
        q = q.in_("competitor_handle", handles)
    response = q.order("viral_score", desc=True).execute()
    data = response.data
    # Client-side filters (Supabase free tier doesn't support array ops easily)
    if hook_types:
        data = [r for r in data if r.get("hook_type") in hook_types]
    if themes:
        data = [r for r in data if r.get("theme") in themes]
    return data


@st.cache_data(ttl=300)
def get_summary(week: str) -> dict | None:
    response = (
        get_client()
        .table("summaries")
        .select("*")
        .eq("week_start_date", week)
        .execute()
    )
    return response.data[0] if response.data else None
```

- [ ] **Step 2: Create dashboard/tabs/viral_overview.py**

```python
# dashboard/tabs/viral_overview.py
import streamlit as st
import pandas as pd
from dashboard.queries import get_reels


def render(week: str, min_score: int):
    st.subheader("🔥 Top Viral Reels Deze Week")
    st.caption(f"Week van {week} · Alle concurrenten · Drempel: viral score ≥ {min_score}")

    reels = get_reels(week=week, min_score=min_score, competitors_only=True)

    if not reels:
        st.info("Geen data gevonden voor deze week. Draai de scraper eerst via GitHub Actions.")
        return

    for reel in reels[:10]:
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=120)
            with col2:
                score_color = "🟢" if reel["viral_score"] >= 70 else "🟡" if reel["viral_score"] >= 50 else "🔴"
                st.markdown(f"**{reel.get('hook', '—')}**  {score_color} `{reel['viral_score']}`")
                st.caption(
                    f"@{reel['competitor_handle']} · "
                    f"{reel.get('theme', '—')} · "
                    f"{reel.get('hook_type', '—')} · "
                    f"👁 {reel.get('views', 0):,} · "
                    f"❤️ {reel.get('likes', 0):,}"
                )
                if reel.get("ai_why"):
                    st.markdown(f"*Waarom: {reel['ai_why']}*")
                if reel.get("ai_your_version"):
                    st.success(f"💡 Jouw versie: {reel['ai_your_version']}")
                if reel.get("video_url"):
                    st.markdown(f"[🔗 Bekijk Reel]({reel['video_url']})")
            st.divider()
```

- [ ] **Step 3: Create dashboard/app.py**

```python
# dashboard/app.py
import streamlit as st
from dashboard.queries import get_available_weeks

st.set_page_config(
    page_title="Content Dashboard — Ayman",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 Content Research Dashboard")
st.caption("Hybrid Performance · @aymanraoul")

# --- Sidebar filters ---
st.sidebar.header("Filters")

weeks = get_available_weeks()
if not weeks:
    st.warning("Geen data gevonden. Voer eerst de scraper uit via GitHub Actions.")
    st.stop()

selected_week = st.sidebar.selectbox("Week", weeks, index=0)
min_score = st.sidebar.slider("Minimale Viral Score", 0, 100, 60)

# --- Tab routing ---
from dashboard.tabs import viral_overview, competitor_breakdown, hook_library, value_content, my_performance, weekly_summary

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔥 Viral Content",
    "👥 Per Concurrent",
    "🪝 Hook Library",
    "💡 Value Content",
    "📈 Mijn Performance",
    "📋 Weekly Summary",
])

with tab1:
    viral_overview.render(selected_week, min_score)
with tab2:
    competitor_breakdown.render(selected_week, min_score)
with tab3:
    hook_library.render(selected_week)
with tab4:
    value_content.render(selected_week)
with tab5:
    my_performance.render(selected_week)
with tab6:
    weekly_summary.render(selected_week)
```

- [ ] **Step 4: Create empty tab files (stubs for remaining tabs)**

```python
# dashboard/tabs/__init__.py
# (empty)
```

```python
# dashboard/__init__.py
# (empty)
```

Create stubs for tabs 2-6 (will be filled in Tasks 11-15):

```python
# dashboard/tabs/competitor_breakdown.py
import streamlit as st
def render(week, min_score):
    st.info("Coming soon: Per Concurrent tab")
```

Copy same stub content to:
- `dashboard/tabs/hook_library.py` → `def render(week):`
- `dashboard/tabs/value_content.py` → `def render(week):`
- `dashboard/tabs/my_performance.py` → `def render(week):`
- `dashboard/tabs/weekly_summary.py` → `def render(week):`

- [ ] **Step 5: Test dashboard locally**

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 — should see the dashboard with Tab 1 rendering (or "Geen data" message if DB is empty).

- [ ] **Step 6: Commit**

```bash
git add dashboard/
git commit -m "feat: streamlit dashboard core + viral overview tab"
```

---

## Task 11: Tab 2 — Per Concurrent

**Files:**
- Modify: `dashboard/tabs/competitor_breakdown.py`

- [ ] **Step 1: Implement competitor_breakdown.py**

```python
# dashboard/tabs/competitor_breakdown.py
import streamlit as st
from dashboard.queries import get_reels

ACCOUNTS = ["williamdurnik", "chrismouton_", "harleysshields", "kvnramirezz", "alexmegino", "kirstyhendey"]


def render(week: str, min_score: int):
    st.subheader("👥 Per Concurrent")

    handle = st.selectbox("Kies account", ACCOUNTS, format_func=lambda h: f"@{h}")
    reels = get_reels(week=week, handles=[handle])

    if not reels:
        st.info(f"Geen data voor @{handle} in week {week}.")
        return

    st.caption(f"{len(reels)} Reels gevonden voor @{handle} · gesorteerd op Viral Score")

    for reel in reels:
        col1, col2 = st.columns([1, 3])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=100)
        with col2:
            score_color = "🟢" if reel["viral_score"] >= 70 else "🟡" if reel["viral_score"] >= 50 else "🔴"
            st.markdown(f"**{reel.get('hook', '—')}**  {score_color} `{reel['viral_score']}`")
            st.caption(
                f"{reel.get('theme', '—')} · {reel.get('hook_type', '—')} · "
                f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,} · "
                f"💬 {reel.get('comments', 0):,}"
            )
            if reel.get("ai_your_version"):
                st.success(f"💡 {reel['ai_your_version']}")
            if reel.get("video_url"):
                st.markdown(f"[🔗 Bekijk]({reel['video_url']})")
        st.divider()
```

- [ ] **Step 2: Test locally**

```bash
streamlit run dashboard/app.py
```

Navigate to "👥 Per Concurrent" tab. Select an account.

- [ ] **Step 3: Commit**

```bash
git add dashboard/tabs/competitor_breakdown.py
git commit -m "feat: per-competitor breakdown tab"
```

---

## Task 12: Tab 3 — Hook Library

**Files:**
- Modify: `dashboard/tabs/hook_library.py`

- [ ] **Step 1: Implement hook_library.py**

```python
# dashboard/tabs/hook_library.py
import streamlit as st
import pandas as pd
from dashboard.queries import get_reels

HOOK_TYPES = ["identiteit", "tegenstelling", "discipline", "transformatie", "lifestyle", "anders"]


def render(week: str):
    st.subheader("🪝 Hook Library")
    st.caption("Hooks gegroepeerd op type · gesorteerd op effectiviteit")

    reels = get_reels(week=week, competitors_only=True)
    if not reels:
        st.info("Geen data voor deze week.")
        return

    selected_type = st.selectbox("Filter op hook-type", ["Alle"] + HOOK_TYPES)
    filtered = reels if selected_type == "Alle" else [r for r in reels if r.get("hook_type") == selected_type]

    # Group by hook_type and show avg score
    df = pd.DataFrame(filtered)
    if df.empty:
        st.info("Geen hooks gevonden.")
        return

    if "hook_type" in df.columns and "viral_score" in df.columns:
        summary = df.groupby("hook_type")["viral_score"].agg(["mean", "count"]).reset_index()
        summary.columns = ["Hook Type", "Gem. Score", "Aantal"]
        summary = summary.sort_values("Gem. Score", ascending=False)
        st.dataframe(summary, use_container_width=True, hide_index=True)

    st.markdown("---")
    for reel in filtered:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.markdown(f"**{reel.get('hook', '—')}**")
        with col2:
            st.caption(reel.get("hook_type", "—"))
        with col3:
            st.caption(f"Score: {reel.get('viral_score', 0)}")
        with col4:
            if reel.get("video_url"):
                st.markdown(f"[🔗]({reel['video_url']})")
```

- [ ] **Step 2: Test + commit**

```bash
streamlit run dashboard/app.py
# Check Hook Library tab
git add dashboard/tabs/hook_library.py
git commit -m "feat: hook library tab with type grouping"
```

---

## Task 13: Tab 4 — Value Content Library

**Files:**
- Modify: `dashboard/tabs/value_content.py`

- [ ] **Step 1: Implement value_content.py**

```python
# dashboard/tabs/value_content.py
import streamlit as st
from dashboard.queries import get_reels

THEMES = ["hybrid", "kracht", "voeding", "mindset", "lifestyle", "anders"]


def render(week: str):
    st.subheader("💡 Value Content Library")
    st.caption("Reels gesorteerd op thema")

    selected_themes = st.multiselect("Filter op thema", THEMES, default=THEMES)
    reels = get_reels(week=week, themes=selected_themes, competitors_only=True)

    if not reels:
        st.info("Geen content gevonden voor deze thema's.")
        return

    for reel in reels:
        col1, col2 = st.columns([1, 3])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=100)
        with col2:
            st.markdown(f"**{reel.get('hook', '—')}**")
            st.caption(
                f"@{reel['competitor_handle']} · {reel.get('theme', '—')} · "
                f"👁 {reel.get('views', 0):,} · Score: {reel.get('viral_score', 0)}"
            )
            if reel.get("ai_your_version"):
                st.success(f"💡 Jouw versie: {reel['ai_your_version']}")
            if reel.get("video_url"):
                st.markdown(f"[🔗 Bekijk]({reel['video_url']})")
        st.divider()
```

- [ ] **Step 2: Test + commit**

```bash
git add dashboard/tabs/value_content.py
git commit -m "feat: value content library tab by theme"
```

---

## Task 14: Tab 5 — Mijn Performance

**Files:**
- Modify: `dashboard/tabs/my_performance.py`

- [ ] **Step 1: Implement my_performance.py**

```python
# dashboard/tabs/my_performance.py
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.queries import get_reels


def render(week: str):
    st.subheader("📈 Mijn Performance — @aymanraoul")

    my_reels = get_reels(own_only=True)  # All time for trend chart
    my_week_reels = get_reels(week=week, own_only=True)
    competitor_reels = get_reels(week=week, competitors_only=True)

    if not my_reels:
        st.info("Nog geen data voor @aymanraoul. Zorg dat 'aymanraoul' in de accounts lijst staat.")
        return

    # Metrics row
    col1, col2, col3 = st.columns(3)
    my_avg = sum(r["viral_score"] for r in my_week_reels) / max(len(my_week_reels), 1)
    comp_avg = sum(r["viral_score"] for r in competitor_reels) / max(len(competitor_reels), 1)

    with col1:
        st.metric("Jouw gem. score deze week", f"{my_avg:.0f}")
    with col2:
        st.metric("Concurrentie gem. score", f"{comp_avg:.0f}")
    with col3:
        diff = my_avg - comp_avg
        st.metric("Verschil", f"{diff:+.0f}", delta_color="normal")

    # Trend chart (all time)
    if len(my_reels) >= 2:
        df = pd.DataFrame(my_reels)
        df["posted_at"] = pd.to_datetime(df["posted_at"])
        df = df.sort_values("posted_at")
        fig = px.line(
            df, x="posted_at", y="viral_score",
            title="Viral Score Over Tijd",
            labels={"posted_at": "Datum", "viral_score": "Viral Score"},
        )
        fig.update_traces(line_color="#4ade80")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # This week's reels
    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info("Geen eigen Reels gescraped voor deze week.")
    else:
        for reel in my_week_reels:
            col1, col2 = st.columns([1, 3])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=100)
            with col2:
                score_color = "🟢" if reel["viral_score"] >= 70 else "🟡" if reel["viral_score"] >= 50 else "🔴"
                st.markdown(f"**{reel.get('hook', '—')}**  {score_color} `{reel['viral_score']}`")
                st.caption(
                    f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,} · "
                    f"💬 {reel.get('comments', 0):,} · {reel.get('posted_at', '')[:10]}"
                )
                if reel.get("video_url"):
                    st.markdown(f"[🔗 Bekijk]({reel['video_url']})")
            st.divider()
```

- [ ] **Step 2: Test + commit**

```bash
git add dashboard/tabs/my_performance.py
git commit -m "feat: my performance tab with trend chart"
```

---

## Task 15: Tab 6 — Weekly Summary

**Files:**
- Modify: `dashboard/tabs/weekly_summary.py`

- [ ] **Step 1: Implement weekly_summary.py**

```python
# dashboard/tabs/weekly_summary.py
import streamlit as st
from dashboard.queries import get_summary, get_available_weeks


def render(week: str):
    st.subheader("📋 Weekly Summary")

    summary = get_summary(week)

    if not summary:
        # Try to show previous week's summary if this week's isn't ready yet
        weeks = get_available_weeks()
        if len(weeks) > 1:
            prev_week = weeks[1]
            summary = get_summary(prev_week)
            if summary:
                st.info(f"Samenvatting van week {week} is nog niet beschikbaar. Samenvatting van {prev_week} getoond.")
            else:
                st.info("Nog geen samenvatting beschikbaar. Wordt aangemaakt na de volgende scrape run.")
                return
        else:
            st.info("Nog geen samenvatting beschikbaar. Wordt aangemaakt na de volgende scrape run.")
            return

    st.markdown("### 📊 Trending Thema's")
    st.markdown(summary.get("trending_themes", "—"))

    st.markdown("### 🪝 Beste Hook-types")
    st.markdown(summary.get("best_hook_types", "—"))

    st.markdown("### 🎯 Top 3 Om Na Te Maken")
    st.markdown(summary.get("top3_to_copy", "—"))

    st.markdown("### 💡 Jouw Contentadvies Deze Week")
    st.success(summary.get("weekly_advice", "—"))

    st.caption(f"Gegenereerd op {summary.get('generated_at', '')[:10]}")
```

- [ ] **Step 2: Test + commit**

```bash
git add dashboard/tabs/weekly_summary.py
git commit -m "feat: weekly summary tab with fallback to previous week"
```

---

## Task 16: Deploy to Streamlit Cloud

- [ ] **Step 1: Push all code to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Deploy on Streamlit Cloud**

1. Go to share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Repository: your repo, Branch: `main`, Main file: `dashboard/app.py`
5. Click "Advanced settings" → Add secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key_here"
```

6. Click "Deploy"

Expected: App is live at `https://your-app.streamlit.app` within 2 minutes.

- [ ] **Step 3: Verify the live dashboard**

Open the Streamlit Cloud URL. Check all 6 tabs load without errors (empty state messages are fine before first scrape).

- [ ] **Step 4: Trigger first manual scrape**

Go to GitHub → Actions → "Weekly Content Scrape" → "Run workflow" → Run.

Wait ~15 minutes, then refresh the dashboard. Data should appear in Tab 1.

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete content dashboard v1.0"
git push origin main
```

---

## Done ✅

The dashboard is live. Every Monday at 06:00 UTC, GitHub Actions automatically scrapes 7 Instagram accounts, runs AI analysis, and updates Supabase. Open the Streamlit URL any time to see this week's viral content, hooks, and your own performance.

**Total cost:** ~€8–10/month (Apify + OpenAI)

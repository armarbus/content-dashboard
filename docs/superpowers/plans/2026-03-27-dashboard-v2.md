# Dashboard v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing dashboard into a content machine: auto-transcribe viral reels, add hashtag discovery, replace verbose reel cards with a shared modal + "Nak dit" script generator, and add a hook/theme performance breakdown.

**Architecture:** Processor gets two new modules (transcriber, hashtag scraping) and a restructured two-pass `run()`. Dashboard gets a shared `reel_modal` component imported by all tabs, a new Niche Discovery tab, and upgraded My Performance charts.

**Tech Stack:** Python 3.11, Streamlit 1.55+, Supabase, OpenAI Whisper + GPT-4o-mini, Apify, Plotly

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `supabase/schema.sql` | Modify | Add `transcript`, `source`, `niche_tag` columns |
| `.github/workflows/weekly_scrape.yml` | Modify | Raise timeout 30→60 min |
| `processor/transcriber.py` | Create | Whisper transcription for top-N reels |
| `processor/apify_client.py` | Modify | Add `fetch_hashtag_reels()` + `DISCOVERY_HASHTAGS` |
| `processor/main.py` | Modify | Two-pass restructure + hashtag step |
| `requirements.txt` (dashboard) | Modify | Add `openai>=1.30.1` |
| `dashboard/components/__init__.py` | Create | Empty package marker |
| `dashboard/components/reel_modal.py` | Create | Shared modal + Nak dit generator |
| `dashboard/tabs/viral_overview.py` | Modify | Compact cards + modal button |
| `dashboard/tabs/competitor_breakdown.py` | Modify | Compact cards + modal button |
| `dashboard/tabs/hook_library.py` | Modify | Compact cards + modal button |
| `dashboard/tabs/value_content.py` | Modify | Compact cards + modal button |
| `dashboard/tabs/my_performance.py` | Modify | Hook/theme breakdown charts |
| `dashboard/tabs/niche_discovery.py` | Create | New hashtag discovery tab |
| `dashboard/app.py` | Modify | Add niche_discovery, 7 tabs total |
| `dashboard/queries.py` | Modify | Add `get_niche_reels()` |

---

## Task 1: Database Migration

**Files:**
- Modify: `supabase/schema.sql`

Add the 3 new columns to the `reels` table. Run this SQL via the Supabase SQL editor.

- [ ] **Step 1: Add the migration SQL to `supabase/schema.sql`**

Append to the existing file:

```sql
-- Dashboard v2 columns
alter table reels add column if not exists transcript text;
alter table reels add column if not exists source text default 'account';
alter table reels add column if not exists niche_tag text
  check (niche_tag is null or niche_tag like '#%');
```

- [ ] **Step 2: Run the migration in Supabase**

Go to Supabase → SQL Editor → paste the 3 ALTER statements → Run.
Expected: success, no errors.

- [ ] **Step 3: Verify columns exist**

Run in SQL Editor:
```sql
select column_name, data_type, column_default
from information_schema.columns
where table_name = 'reels'
  and column_name in ('transcript', 'source', 'niche_tag');
```
Expected: 3 rows returned.

- [ ] **Step 4: Commit**

```bash
git add supabase/schema.sql
git commit -m "feat: add transcript, source, niche_tag columns to reels"
```

---

## Task 2: GitHub Actions Timeout

**Files:**
- Modify: `.github/workflows/weekly_scrape.yml`

- [ ] **Step 1: Update timeout**

Change line 10:
```yaml
    timeout-minutes: 60
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/weekly_scrape.yml
git commit -m "feat: raise GH Actions timeout to 60 min for transcription"
```

---

## Task 3: Transcription Module

**Files:**
- Create: `processor/transcriber.py`

This module downloads the top-N reels by viral score and transcribes them with Whisper.

Key rules from spec:
- Skip if `video_url` is None
- `HEAD` request first to verify `Content-Type: video/*` — skip if not video
- Download to `tempfile.NamedTemporaryFile(suffix='.mp4')`
- Call `openai.audio.transcriptions.create(model="whisper-1", file=fp)`
- `finally` block always deletes temp file
- Any exception: log warning, `continue` (non-fatal)

- [ ] **Step 1: Create `processor/transcriber.py`**

```python
# processor/transcriber.py
"""
Transcribes top-N reels by viral_score using OpenAI Whisper.
Non-fatal: exceptions per reel are logged and skipped.
"""
import os
import tempfile
import requests
from openai import OpenAI

TOP_N_TRANSCRIBE = 20  # single source of truth, imported by main.py


def transcribe_top_reels(scored_reels: list[dict], top_n: int = TOP_N_TRANSCRIBE) -> dict[str, str]:
    """
    Downloads and transcribes the top_n reels by viral_score.
    Returns dict mapping reel_id -> transcript text.
    Only processes reels with a direct video URL (Content-Type: video/*).
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    sorted_reels = sorted(scored_reels, key=lambda r: r.get("viral_score", 0), reverse=True)
    candidates = sorted_reels[:top_n]

    transcripts: dict[str, str] = {}

    for reel in candidates:
        reel_id = reel.get("reel_id", "")
        video_url = reel.get("video_url")

        if not video_url:
            continue

        # Skip obvious Instagram page URLs (not direct video files)
        if "instagram.com/reel/" in video_url and ".mp4" not in video_url:
            continue

        tmp_path = None
        try:
            # Verify Content-Type before downloading
            head = requests.head(video_url, timeout=10, allow_redirects=True)
            content_type = head.headers.get("Content-Type", "")
            if not content_type.startswith("video/"):
                print(f"  ⚠️  Skipping {reel_id}: Content-Type={content_type!r}")
                continue

            # Download to temp file
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)

            # Transcribe
            with open(tmp_path, "rb") as fp:
                result = client.audio.transcriptions.create(model="whisper-1", file=fp)
            transcripts[reel_id] = result.text
            print(f"  ✅ Transcribed {reel_id}: {result.text[:60]}...")

        except Exception as e:
            print(f"  ⚠️  Transcription failed for {reel_id}: {e}")
            continue

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return transcripts
```

- [ ] **Step 2: Verify import works**

```bash
cd /path/to/project && python -c "from processor.transcriber import TOP_N_TRANSCRIBE, transcribe_top_reels; print(TOP_N_TRANSCRIBE)"
```
Expected: `20`

- [ ] **Step 3: Commit**

```bash
git add processor/transcriber.py
git commit -m "feat: add Whisper transcription module (top-20 reels)"
```

---

## Task 4: Hashtag Discovery in Apify Client

**Files:**
- Modify: `processor/apify_client.py`

Add `DISCOVERY_HASHTAGS` list and `fetch_hashtag_reels()` function. The Apify instagram-scraper actor uses `"hashtags"` key (not `directUrls`) for hashtag scraping.

- [ ] **Step 1: Add to `processor/apify_client.py`**

After the existing `ACTOR_ID` and `ACCOUNTS` definitions, add:

```python
DISCOVERY_HASHTAGS = ["hybridtraining"]  # extend list to add more hashtags
```

Then after the `fetch_all_accounts()` function, add:

```python
def fetch_hashtag_reels(hashtag: str, max_results: int = 20) -> list[dict]:
    """
    Fetches up to max_results reels for a given hashtag via Apify.
    Returns a list of parsed dicts ready for scoring/analysis.
    """
    client = ApifyClient(os.environ["APIFY_API_TOKEN"])
    run_input = {
        "hashtags": [hashtag],
        "resultsType": "posts",
        "resultsLimit": max_results,
        "addParentData": False,
    }
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    parsed = []
    for raw in items:
        p = parse_reel(raw, handle=raw.get("ownerUsername", "unknown"), is_own=False)
        if p and p["reel_id"]:
            p["source"] = "hashtag"
            p["niche_tag"] = f"#{hashtag}"
            parsed.append(p)
    return parsed
```

- [ ] **Step 2: Verify import**

```bash
python -c "from processor.apify_client import DISCOVERY_HASHTAGS, fetch_hashtag_reels; print(DISCOVERY_HASHTAGS)"
```
Expected: `['hybridtraining']`

- [ ] **Step 3: Commit**

```bash
git add processor/apify_client.py
git commit -m "feat: add hashtag discovery scraping to apify client"
```

---

## Task 5: Restructure `main.py` (Two-Pass + Hashtag)

**Files:**
- Modify: `processor/main.py`

Restructure `run()` into 5 passes:
1. Collect + Score + Analyze all account reels → `all_records` (no upsert yet)
2. Transcribe top 20 → attach `transcript` to records
3. Upsert all records
4. Hashtag discovery (fetch → score → analyze → upsert, no transcription)
5. Weekly summary (unchanged)

- [ ] **Step 1: Rewrite `processor/main.py`**

```python
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
```

- [ ] **Step 2: Verify import**

```bash
python -c "from processor.main import run; print('OK')"
```
Expected: `OK` (no import errors)

- [ ] **Step 3: Commit**

```bash
git add processor/main.py
git commit -m "feat: two-pass main.py with transcription + hashtag discovery"
```

---

## Task 6: Dashboard Requirements

**Files:**
- Modify: `requirements.txt` (the dashboard requirements file — check if it's named `requirements.txt` or `requirements-dashboard.txt`)

- [ ] **Step 1: Find the dashboard requirements file**

```bash
ls /path/to/project/*.txt
```
Look for the file used by Streamlit Cloud (usually `requirements.txt` in root).

- [ ] **Step 2: Add openai dependency**

Add to the file (if not already present):
```
openai>=1.30.1
```

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add openai to dashboard requirements for Nak dit generator"
```

---

## Task 7: Reel Modal Component

**Files:**
- Create: `dashboard/components/__init__.py`
- Create: `dashboard/components/reel_modal.py`

This is the heart of v2. All tabs call `show_reel_modal(reel)` to open the detail view.

**Modal layout:**
- Left col (40%): thumbnail + Instagram link button
- Right col (60%): handle, date, score badge, hook, hook_type chip, theme chip, views/likes/comments, ai_why, transcript expander (only if transcript exists), divider, "Nak dit" button

**"Nak dit" output format:**
```
**Hook:** [opening line]
**Punt 1:** [...]
**Punt 2:** [...]
**Punt 3:** [...]
**CTA:** [call to action]
```

**Session state caching:** `cache_key = f"nakit_{reel['reel_id']}"` — prevents duplicate API calls on re-clicks.

- [ ] **Step 1: Create `dashboard/components/__init__.py`**

```python
# dashboard/components/__init__.py
```
(empty file)

- [ ] **Step 2: Create `dashboard/components/reel_modal.py`**

```python
# dashboard/components/reel_modal.py
"""
Shared modal component for reel detail view + Nak dit script generator.
Imported by all tab modules.
"""
import os
import streamlit as st
from openai import OpenAI

NAKIT_SYSTEM_PROMPT = """Je bent een content strateeg voor Ayman, een hybrid performance coach.
Zijn doelgroep: mannen 16-35. Merk: hybrid training, discipline, masculinity, lifestyle.
Schrijf een volledig Reel-script op basis van een viral reel van een concurrent.
Output exact dit formaat (geen extra tekst):
**Hook:** [opening line — eerste 3 seconden]
**Punt 1:** [eerste punt of actie — 5-10 seconden]
**Punt 2:** [tweede punt of actie — 5-10 seconden]
**Punt 3:** [derde punt of actie — 5-10 seconden]
**CTA:** [call to action — laatste 3 seconden]
Schrijf in het Nederlands. Wees direct, energiek, masculine."""


def generate_nakit_script(reel: dict) -> str:
    """Calls OpenAI to generate a Nak dit script for the given reel."""
    client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", ""))

    transcript_section = ""
    if reel.get("transcript"):
        transcript_section = f"\nTranscriptie: {reel['transcript'][:500]}"

    user_prompt = (
        f"Viral reel van @{reel.get('competitor_handle', 'onbekend')}:\n"
        f"Hook: {reel.get('hook', '')}\n"
        f"Thema: {reel.get('theme', '')}\n"
        f"Hook type: {reel.get('hook_type', '')}\n"
        f"Waarom viral: {reel.get('ai_why', '')}\n"
        f"Views: {reel.get('views', 0):,}{transcript_section}\n\n"
        "Schrijf nu Ayman's versie van dit script."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": NAKIT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=400,
    )
    return response.choices[0].message.content


@st.dialog("Reel details", width="large")
def show_reel_modal(reel: dict):
    """Full-detail modal for a single reel, with Nak dit script generator."""
    col_left, col_right = st.columns([2, 3])

    with col_left:
        if reel.get("thumbnail_url"):
            st.image(reel["thumbnail_url"], use_container_width=True)
        if reel.get("video_url"):
            st.link_button("🔗 Bekijk op Instagram", reel["video_url"])

    with col_right:
        score = reel.get("viral_score", 0)
        badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"

        st.markdown(f"**@{reel.get('competitor_handle', '—')}** · {str(reel.get('posted_at', ''))[:10]}")
        st.markdown(f"{badge} Viral Score: **{score}**")

        st.markdown(f"**Hook:** {reel.get('hook', '—')}")
        col_chips1, col_chips2 = st.columns(2)
        with col_chips1:
            st.caption(f"Type: `{reel.get('hook_type', '—')}`")
        with col_chips2:
            st.caption(f"Thema: `{reel.get('theme', '—')}`")

        cols = st.columns(3)
        cols[0].metric("Views", f"{reel.get('views', 0):,}")
        cols[1].metric("Likes", f"{reel.get('likes', 0):,}")
        cols[2].metric("Comments", f"{reel.get('comments', 0):,}")

        if reel.get("ai_why"):
            st.markdown(f"**Waarom viral:** {reel['ai_why']}")

        if reel.get("transcript"):
            with st.expander("📝 Transcriptie"):
                st.text(reel["transcript"])

        st.divider()

        cache_key = f"nakit_{reel['reel_id']}"
        if st.button("🚀 Nak dit", type="primary"):
            if cache_key not in st.session_state:
                with st.spinner("Script genereren..."):
                    try:
                        st.session_state[cache_key] = generate_nakit_script(reel)
                    except Exception as e:
                        st.error(f"Script genereren mislukt: {e}")

        if cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])
```

- [ ] **Step 3: Verify import**

```bash
python -c "from dashboard.components.reel_modal import show_reel_modal; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add dashboard/components/__init__.py dashboard/components/reel_modal.py
git commit -m "feat: add shared reel modal with Nak dit script generator"
```

---

## Task 8: Compact Card Refactor — All 4 Existing Tabs

**Files:**
- Modify: `dashboard/tabs/viral_overview.py`
- Modify: `dashboard/tabs/competitor_breakdown.py`
- Modify: `dashboard/tabs/hook_library.py`
- Modify: `dashboard/tabs/value_content.py`

Replace the two-column verbose cards with: small thumbnail (120px) + truncated hook + score badge + "🔍 Bekijk" button that opens the modal.

- [ ] **Step 1: Rewrite `dashboard/tabs/viral_overview.py`**

```python
# dashboard/tabs/viral_overview.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal


def render(week, min_score):
    st.subheader("Top Viral Reels Deze Week")
    st.caption(f"Week van {week} · Alle concurrenten · Drempel: viral score ≥ {min_score}")

    reels = get_reels(week=week, min_score=min_score, competitors_only=True)

    if not reels:
        st.info("Geen data gevonden voor deze week. Draai de scraper eerst via GitHub Actions → Run workflow.")
        return

    for reel in reels[:20]:
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            hook = reel.get("hook", "—")
            st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
            st.caption(f"@{reel['competitor_handle']} · {reel.get('theme', '—')} · {reel.get('hook_type', '—')}")
        with col3:
            if st.button("🔍 Bekijk", key=f"vo_{reel['reel_id']}"):
                show_reel_modal(reel)
        st.divider()
```

- [ ] **Step 2: Rewrite `dashboard/tabs/competitor_breakdown.py`**

```python
# dashboard/tabs/competitor_breakdown.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal

ACCOUNTS = ["williamdurnik", "chrismouton_", "harleysshields", "kvnramirezz", "alexmegino", "kirstyhendey"]


def render(week, min_score):
    st.subheader("Per Concurrent")

    handle = st.selectbox("Kies account", ACCOUNTS, format_func=lambda h: f"@{h}")
    reels = get_reels(week=week, handles=[handle], min_score=min_score)

    if not reels:
        st.info(f"Geen data voor @{handle} in week {week}.")
        return

    st.caption(f"{len(reels)} Reels voor @{handle} · gesorteerd op Viral Score")

    for reel in reels:
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            hook = reel.get("hook", "—")
            st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
            st.caption(f"{reel.get('theme', '—')} · {reel.get('hook_type', '—')} · 👁 {reel.get('views', 0):,}")
        with col3:
            if st.button("🔍 Bekijk", key=f"cb_{reel['reel_id']}"):
                show_reel_modal(reel)
        st.divider()
```

- [ ] **Step 3: Rewrite `dashboard/tabs/hook_library.py`**

```python
# dashboard/tabs/hook_library.py
import streamlit as st
import pandas as pd
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal

HOOK_TYPES = ["identiteit", "tegenstelling", "discipline", "transformatie", "lifestyle", "anders"]


def render(week):
    st.subheader("Hook Library")
    st.caption("Hooks gegroepeerd op type · gesorteerd op effectiviteit")

    reels = get_reels(week=week, competitors_only=True)
    if not reels:
        st.info("Geen data voor deze week.")
        return

    selected_type = st.selectbox("Filter op hook-type", ["Alle"] + HOOK_TYPES)
    filtered = reels if selected_type == "Alle" else [r for r in reels if r.get("hook_type") == selected_type]

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
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            hook = reel.get("hook", "—")
            st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** `{score}`")
            st.caption(f"`{reel.get('hook_type', '—')}` · @{reel.get('competitor_handle', '—')}")
        with col3:
            if st.button("🔍 Bekijk", key=f"hl_{reel['reel_id']}"):
                show_reel_modal(reel)
        st.divider()
```

- [ ] **Step 4: Rewrite `dashboard/tabs/value_content.py`**

```python
# dashboard/tabs/value_content.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal

THEMES = ["hybrid", "kracht", "voeding", "mindset", "lifestyle", "anders"]


def render(week):
    st.subheader("Value Content Library")
    st.caption("Reels gesorteerd op thema")

    selected_themes = st.multiselect("Filter op thema", THEMES, default=THEMES)
    reels = get_reels(week=week, themes=selected_themes, competitors_only=True)

    if not reels:
        st.info("Geen content gevonden voor deze thema's.")
        return

    for reel in reels:
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            hook = reel.get("hook", "—")
            st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** `{score}`")
            st.caption(f"@{reel['competitor_handle']} · `{reel.get('theme', '—')}` · 👁 {reel.get('views', 0):,}")
        with col3:
            if st.button("🔍 Bekijk", key=f"vc_{reel['reel_id']}"):
                show_reel_modal(reel)
        st.divider()
```

- [ ] **Step 5: Commit**

```bash
git add dashboard/tabs/viral_overview.py dashboard/tabs/competitor_breakdown.py \
        dashboard/tabs/hook_library.py dashboard/tabs/value_content.py
git commit -m "feat: replace verbose reel cards with compact modal-linked cards"
```

---

## Task 9: Niche Discovery Tab

**Files:**
- Modify: `dashboard/queries.py` — add `get_niche_reels()`
- Create: `dashboard/tabs/niche_discovery.py`

- [ ] **Step 1: Add `get_niche_reels()` to `dashboard/queries.py`**

Add after the existing `get_summary()` function:

```python
@st.cache_data(ttl=300)
def get_niche_reels(week=None, min_score=0):
    """Fetches reels scraped via hashtag discovery (source='hashtag')."""
    q = get_client().table("reels").select("*").eq("source", "hashtag")
    if week:
        q = q.eq("week_start_date", week)
    if min_score > 0:
        q = q.gte("viral_score", min_score)
    response = q.order("viral_score", desc=True).execute()
    return response.data
```

- [ ] **Step 2: Create `dashboard/tabs/niche_discovery.py`**

```python
# dashboard/tabs/niche_discovery.py
import streamlit as st
from dashboard.queries import get_niche_reels
from dashboard.components.reel_modal import show_reel_modal


def render(week, min_score):
    st.subheader("Niche Discovery")

    reels = get_niche_reels(week=week, min_score=min_score)

    if not reels:
        st.info("Nog geen hashtag-reels voor deze week. Ze worden toegevoegd bij de volgende wekelijkse scrape.")
        return

    # Group by niche_tag
    tags = sorted(set(r.get("niche_tag", "#onbekend") for r in reels))
    for tag in tags:
        tag_reels = [r for r in reels if r.get("niche_tag") == tag]
        st.markdown(f"### Viral in {tag} deze week")
        st.caption(f"{len(tag_reels)} reels gevonden · min score {min_score}")

        for reel in tag_reels:
            col1, col2, col3 = st.columns([1, 6, 1])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=120)
            with col2:
                score = reel.get("viral_score", 0)
                badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                hook = reel.get("hook", "—")
                st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
                st.caption(f"@{reel.get('competitor_handle', '—')} · {reel.get('theme', '—')} · {reel.get('hook_type', '—')}")
            with col3:
                if st.button("🔍 Bekijk", key=f"nd_{reel['reel_id']}"):
                    show_reel_modal(reel)
            st.divider()
```

- [ ] **Step 3: Commit**

```bash
git add dashboard/queries.py dashboard/tabs/niche_discovery.py
git commit -m "feat: add niche discovery tab + get_niche_reels query"
```

---

## Task 10: My Performance Upgrade (Hook + Theme Charts)

**Files:**
- Modify: `dashboard/tabs/my_performance.py`

Add two grouped bar charts comparing Ayman vs competitor avg per hook_type and per theme. Apply minimum sample size rule: only show bars where Ayman has ≥3 reels, else show greyed placeholder. Add auto-insight text under each chart.

- [ ] **Step 1: Rewrite `dashboard/tabs/my_performance.py`**

```python
# dashboard/tabs/my_performance.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal

MIN_SAMPLE = 3  # minimum own-reel count per hook_type/theme to show bar


def _grouped_bar_chart(my_df: pd.DataFrame, comp_df: pd.DataFrame, group_col: str, title: str):
    """Returns a Plotly figure comparing avg viral score for Ayman vs competitors per group."""
    my_agg = my_df.groupby(group_col)["viral_score"].agg(["mean", "count"]).reset_index()
    my_agg.columns = [group_col, "my_avg", "my_count"]

    comp_agg = comp_df.groupby(group_col)["viral_score"].mean().reset_index()
    comp_agg.columns = [group_col, "comp_avg"]

    merged = my_agg.merge(comp_agg, on=group_col, how="outer").fillna(0)

    fig = go.Figure()

    for _, row in merged.iterrows():
        label = row[group_col]
        if row["my_count"] >= MIN_SAMPLE:
            fig.add_trace(go.Bar(
                name=f"Jij ({label})",
                x=[label], y=[row["my_avg"]],
                marker_color="#4ade80",
                showlegend=False,
            ))
        else:
            fig.add_trace(go.Bar(
                name=f"Jij ({label})",
                x=[label], y=[row["my_avg"] if row["my_count"] > 0 else 0],
                marker_color="#374151",
                text=[f"te weinig data (n={int(row['my_count'])})"],
                textposition="inside",
                showlegend=False,
            ))
        fig.add_trace(go.Bar(
            name=f"Concurrenten ({label})",
            x=[label], y=[row["comp_avg"]],
            marker_color="#6b7280",
            showlegend=False,
        ))

    fig.update_layout(
        title=title,
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Gem. Viral Score",
    )
    return fig, merged


def render(week):
    st.subheader("Mijn Performance — @aymanraoul")

    my_reels = get_reels(own_only=True)
    my_week_reels = get_reels(week=week, own_only=True)
    competitor_reels = get_reels(week=week, competitors_only=True)

    if not my_reels:
        st.info("Nog geen data voor @aymanraoul. Zorg dat de scraper gedraaid heeft.")
        return

    # Section 1 — KPI cards
    col1, col2, col3 = st.columns(3)
    my_avg = sum(r["viral_score"] for r in my_week_reels) / max(len(my_week_reels), 1)
    comp_avg = sum(r["viral_score"] for r in competitor_reels) / max(len(competitor_reels), 1)
    diff = my_avg - comp_avg

    with col1:
        st.metric("Jouw gem. score", f"{my_avg:.0f}")
    with col2:
        st.metric("Concurrentie gem.", f"{comp_avg:.0f}")
    with col3:
        st.metric("Verschil", f"{diff:+.0f}")

    # Trend chart (all time)
    if len(my_reels) >= 2:
        df_all = pd.DataFrame(my_reels)
        df_all["posted_at"] = pd.to_datetime(df_all["posted_at"], errors="coerce")
        df_all = df_all.dropna(subset=["posted_at"]).sort_values("posted_at")
        import plotly.express as px
        fig = px.line(
            df_all, x="posted_at", y="viral_score",
            title="Viral Score Over Tijd",
            labels={"posted_at": "Datum", "viral_score": "Viral Score"},
        )
        fig.update_traces(line_color="#4ade80")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Section 2 — Hook type breakdown
    if my_reels and competitor_reels:
        st.markdown("### Hook Type Breakdown")
        my_df = pd.DataFrame(my_reels)
        comp_df = pd.DataFrame(competitor_reels)

        fig_hook, hook_merged = _grouped_bar_chart(my_df, comp_df, "hook_type", "Jij vs Concurrenten per Hook Type")
        st.plotly_chart(fig_hook, use_container_width=True)

        # Auto-insight
        qualified = hook_merged[hook_merged["my_count"] >= MIN_SAMPLE]
        if not qualified.empty:
            qualified = qualified.copy()
            qualified["diff"] = qualified["my_avg"] - qualified["comp_avg"]
            best = qualified.loc[qualified["diff"].idxmax()]
            st.success(f"✅ Je scoort **{best['diff']:.0f}pt** beter op **{best['hook_type']}** hooks → post er meer van")

    # Section 3 — Theme breakdown
    if my_reels and competitor_reels:
        st.markdown("### Thema Breakdown")
        fig_theme, theme_merged = _grouped_bar_chart(my_df, comp_df, "theme", "Jij vs Concurrenten per Thema")
        st.plotly_chart(fig_theme, use_container_width=True)

        # Auto-insight: find weakest theme
        qualified_theme = theme_merged[theme_merged["my_count"] >= MIN_SAMPLE]
        if not qualified_theme.empty:
            worst = qualified_theme.loc[qualified_theme["my_avg"].idxmin()]
            st.warning(f"⚠️ Je **{worst['theme']}** content scoort zwak (gem. {worst['my_avg']:.0f}) → test een andere aanpak")

    # Section 4 — Weekly reels
    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info("Geen eigen Reels gescraped voor deze week.")
    else:
        for reel in my_week_reels:
            col1, col2, col3 = st.columns([1, 6, 1])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=120)
            with col2:
                score = reel.get("viral_score", 0)
                badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                hook = reel.get("hook", "—")
                st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
                st.caption(
                    f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,} · "
                    f"💬 {reel.get('comments', 0):,} · {str(reel.get('posted_at', ''))[:10]}"
                )
            with col3:
                if st.button("🔍 Bekijk", key=f"mp_{reel['reel_id']}"):
                    show_reel_modal(reel)
            st.divider()
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/tabs/my_performance.py
git commit -m "feat: add hook/theme breakdown charts to My Performance tab"
```

---

## Task 11: Wire Up 7-Tab App

**Files:**
- Modify: `dashboard/app.py`

Add `niche_discovery` import and insert as Tab 2, shifting existing tabs right (7 total).

- [ ] **Step 1: Rewrite `dashboard/app.py`**

```python
# dashboard/app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dashboard.queries import get_available_weeks
from dashboard.tabs import (
    viral_overview, niche_discovery, competitor_breakdown,
    hook_library, value_content, my_performance, weekly_summary,
)

st.set_page_config(
    page_title="Content Dashboard — Ayman",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 Content Research Dashboard")
st.caption("Hybrid Performance · @aymanraoul")

st.sidebar.header("Filters")

weeks = get_available_weeks()
if not weeks:
    st.warning("Geen data gevonden. Voer eerst de scraper uit via GitHub Actions → Run workflow.")
    st.stop()

selected_week = st.sidebar.selectbox("Week", weeks, index=0)
min_score = st.sidebar.slider("Minimale Viral Score", 0, 100, 60)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔥 Viral Content",
    "🔍 Niche Discovery",
    "👥 Per Concurrent",
    "🪝 Hook Library",
    "💡 Value Content",
    "📈 Mijn Performance",
    "📋 Weekly Summary",
])

with tab1:
    viral_overview.render(selected_week, min_score)
with tab2:
    niche_discovery.render(selected_week, min_score)
with tab3:
    competitor_breakdown.render(selected_week, min_score)
with tab4:
    hook_library.render(selected_week)
with tab5:
    value_content.render(selected_week)
with tab6:
    my_performance.render(selected_week)
with tab7:
    weekly_summary.render(selected_week)
```

- [ ] **Step 2: Commit**

```bash
git add dashboard/app.py
git commit -m "feat: add niche discovery tab, wire up 7-tab app"
```

---

## Task 12: Add OPENAI_API_KEY to Streamlit Cloud Secrets

The dashboard's "Nak dit" generator needs `OPENAI_API_KEY` in Streamlit Cloud secrets.

- [ ] **Step 1: Add secret in Streamlit Cloud**

Go to Streamlit Cloud → your app → Settings → Secrets → add:
```toml
OPENAI_API_KEY = "sk-..."
```

- [ ] **Step 2: Verify by opening the dashboard and clicking "Nak dit" on any reel**

---

## Task 13: Push and Test

- [ ] **Step 1: Push all commits**

```bash
git push origin main
```

- [ ] **Step 2: Verify Streamlit Cloud redeploys successfully**

Check the Streamlit Cloud app logs — no import errors, all 7 tabs load.

- [ ] **Step 3: Trigger manual GitHub Actions run**

Go to GitHub → Actions → Weekly Content Scrape → Run workflow.
Monitor the run — confirm it completes within 60 min with no errors.
After run: open dashboard → check Niche Discovery tab shows #hybridtraining reels.

---

## Rollback Notes

If transcription causes the pipeline to time out or error:
- Set `TOP_N_TRANSCRIBE = 0` in `processor/transcriber.py` to disable transcription without code changes
- The `transcript` column will stay `null` for all reels — modal just hides the expander

If hashtag scraping fails:
- Set `DISCOVERY_HASHTAGS = []` in `processor/apify_client.py` to skip
- Niche Discovery tab shows empty state gracefully

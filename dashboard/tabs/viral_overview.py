# dashboard/tabs/viral_overview.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card


def render(week, min_score):
    st.subheader("Top Viral Reels Deze Week")
    st.caption(f"Week van {week} · Alle concurrenten · Drempel: viral score ≥ {min_score}")

    reels = get_reels(week=week, min_score=min_score, competitors_only=True)
    all_week = get_reels(week=week, competitors_only=True)

    if not reels:
        st.info("Geen data gevonden voor deze week. Draai de scraper eerst via GitHub Actions → Run workflow.")
        return

    # ── KPI row ──────────────────────────────────────────────────────────
    avg_score = sum(r["viral_score"] for r in all_week) / max(len(all_week), 1)
    top_views = max((r.get("views", 0) for r in reels), default=0)
    handles = [r.get("competitor_handle", "") for r in all_week]
    top_handle = max(set(handles), key=handles.count) if handles else "—"

    col1, col2, col3, col4 = st.columns(4)
    display_handle = f"{top_handle[:11]}…" if len(top_handle) > 12 else top_handle
    col1.metric("REELS GESCRAPED", len(all_week))
    col2.metric("GEM. VIRAL SCORE", f"{avg_score:.0f}")
    col3.metric("TOP VIEWS", f"{top_views:,}")
    col4.metric("MEEST ACTIEF", f"@{display_handle}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for reel in reels[:20]:
        render_reel_card(reel, button_key=f"vo_{reel['reel_id']}")

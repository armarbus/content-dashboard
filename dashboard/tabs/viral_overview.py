# dashboard/tabs/viral_overview.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card


def render(week, min_score):
    st.subheader("Top Viral Reels Deze Week")
    st.caption(f"Week van {week} · Alle concurrenten · Drempel: viral score ≥ {min_score}")

    reels = get_reels(week=week, min_score=min_score, competitors_only=True)

    if not reels:
        st.info("Geen data gevonden voor deze week. Draai de scraper eerst via GitHub Actions → Run workflow.")
        return

    for reel in reels[:20]:
        render_reel_card(reel, button_key=f"vo_{reel['reel_id']}")

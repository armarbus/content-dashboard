# dashboard/tabs/competitor_breakdown.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card

ACCOUNTS = [
    "williamdurnik", "chrismouton_", "harleysshields",
    "kvnramirezz", "alexmegino", "kirstyhendey",
    "fit.dad.phil", "ferguscrawley", "matt_zelaya",
    "alecblenis", "alex_kukla", "cchungy_",
    "ronencaspers",
]


def render(week, min_score):
    st.subheader("Per Concurrent")

    handle = st.selectbox("Kies account", ACCOUNTS, format_func=lambda h: f"@{h}")
    reels = get_reels(week=week, handles=[handle], min_score=min_score)

    if not reels:
        st.info(f"Geen data voor @{handle} in week {week}.")
        return

    st.caption(f"{len(reels)} Reels voor @{handle} · gesorteerd op Viral Score")

    for reel in reels:
        render_reel_card(reel, button_key=f"cb_{reel['reel_id']}")

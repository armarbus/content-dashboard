# dashboard/tabs/value_content.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card

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
        render_reel_card(reel, button_key=f"vc_{reel['reel_id']}")

# dashboard/tabs/niche_discovery.py
import streamlit as st
from dashboard.queries import get_niche_reels
from dashboard.components.reel_card import render_reel_card


def render(week, min_score):
    st.subheader("Niche Discovery")

    reels = get_niche_reels(week=week, min_score=min_score)

    if not reels:
        st.info("Nog geen hashtag-reels voor deze week. Ze worden toegevoegd bij de volgende wekelijkse scrape.")
        return

    tags = sorted(set(r.get("niche_tag", "#onbekend") for r in reels))
    for tag in tags:
        tag_reels = [r for r in reels if r.get("niche_tag") == tag]

        st.markdown(
            f'<h3 style="font-size:16px;font-weight:700;margin:20px 0 4px 0">'
            f'Viral in <span style="color:#4ade80">{tag}</span> deze week</h3>',
            unsafe_allow_html=True,
        )
        st.caption(f"{len(tag_reels)} reels gevonden · min score {min_score}")

        for reel in tag_reels:
            render_reel_card(reel, button_key=f"nd_{reel['reel_id']}")

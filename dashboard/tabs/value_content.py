# dashboard/tabs/value_content.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card

THEMES = ["hybrid", "kracht", "voeding", "mindset", "lifestyle", "anders"]


def render(week):
    st.subheader("Value Content Library")
    st.caption("Alleen educatieve reels — how-to, uitleg, tips, mindset met narration. Muziek + tekst wordt gefilterd.")

    selected_themes = st.multiselect("Filter op thema", THEMES, default=THEMES)
    reels = get_reels(week=week, themes=selected_themes, competitors_only=True, value_only=True)
    all_reels = get_reels(week=week, themes=selected_themes, competitors_only=True)

    if not all_reels:
        st.info("Geen content gevonden voor deze thema's.")
        return

    top_funnel_count = len([r for r in all_reels if r.get("content_type") == "top_funnel"])
    unclassified_count = len([r for r in all_reels if r.get("content_type") is None])

    col1, col2, col3 = st.columns(3)
    col1.metric("VALUE CONTENT", len(reels))
    col2.metric("TOP FUNNEL (gefilterd)", top_funnel_count)
    col3.metric("NIET GECLASSIFICEERD", unclassified_count,
                help="Geclassificeerd na de volgende scrape")

    if unclassified_count > 0 and not reels:
        st.info(
            f"{unclassified_count} reels zijn nog niet geclassificeerd. "
            "Na de volgende wekelijkse scrape wordt elk reel automatisch gelabeld als "
            "value of top-funnel."
        )
        return

    if not reels:
        st.info("Geen value content gevonden deze week. Top-funnel reels zijn gefilterd.")
        return

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for reel in reels:
        render_reel_card(reel, button_key=f"vc_{reel['reel_id']}")

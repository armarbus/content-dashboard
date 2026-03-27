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

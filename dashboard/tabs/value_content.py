# dashboard/tabs/value_content.py
import streamlit as st
from dashboard.queries import get_reels

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

# dashboard/tabs/hook_library.py
import streamlit as st
import pandas as pd
from dashboard.queries import get_reels

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

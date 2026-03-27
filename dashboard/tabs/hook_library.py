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

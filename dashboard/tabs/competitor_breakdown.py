# dashboard/tabs/competitor_breakdown.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal

ACCOUNTS = ["williamdurnik", "chrismouton_", "harleysshields", "kvnramirezz", "alexmegino", "kirstyhendey"]


def render(week, min_score):
    st.subheader("Per Concurrent")

    handle = st.selectbox("Kies account", ACCOUNTS, format_func=lambda h: f"@{h}")
    reels = get_reels(week=week, handles=[handle], min_score=min_score)

    if not reels:
        st.info(f"Geen data voor @{handle} in week {week}.")
        return

    st.caption(f"{len(reels)} Reels voor @{handle} · gesorteerd op Viral Score")

    for reel in reels:
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            hook = reel.get("hook", "—")
            st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
            st.caption(f"{reel.get('theme', '—')} · {reel.get('hook_type', '—')} · 👁 {reel.get('views', 0):,}")
        with col3:
            if st.button("🔍 Bekijk", key=f"cb_{reel['reel_id']}"):
                show_reel_modal(reel)
        st.divider()

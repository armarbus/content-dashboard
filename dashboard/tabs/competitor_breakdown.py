# dashboard/tabs/competitor_breakdown.py
import streamlit as st
from dashboard.queries import get_reels

ACCOUNTS = ["williamdurnik", "chrismouton_", "harleysshields", "kvnramirezz", "alexmegino", "kirstyhendey"]


def render(week, min_score):
    st.subheader("Per Concurrent")

    handle = st.selectbox("Kies account", ACCOUNTS, format_func=lambda h: f"@{h}")
    reels = get_reels(week=week, handles=[handle])

    if not reels:
        st.info(f"Geen data voor @{handle} in week {week}.")
        return

    st.caption(f"{len(reels)} Reels voor @{handle} · gesorteerd op Viral Score")

    for reel in reels:
        col1, col2 = st.columns([1, 3])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=100)
        with col2:
            score = reel.get("viral_score", 0)
            badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            st.markdown(f"**{reel.get('hook', '—')}** {badge} `{score}`")
            st.caption(
                f"{reel.get('theme', '—')} · {reel.get('hook_type', '—')} · "
                f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,} · 💬 {reel.get('comments', 0):,}"
            )
            if reel.get("ai_your_version"):
                st.success(f"💡 {reel['ai_your_version']}")
            if reel.get("video_url"):
                st.markdown(f"[🔗 Bekijk]({reel['video_url']})")
        st.divider()

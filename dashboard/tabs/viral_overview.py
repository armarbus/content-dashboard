# dashboard/tabs/viral_overview.py
import streamlit as st
from dashboard.queries import get_reels


def render(week, min_score):
    st.subheader("Top Viral Reels Deze Week")
    st.caption(f"Week van {week} · Alle concurrenten · Drempel: viral score ≥ {min_score}")

    reels = get_reels(week=week, min_score=min_score, competitors_only=True)

    if not reels:
        st.info("Geen data gevonden voor deze week. Draai de scraper eerst via GitHub Actions → Run workflow.")
        return

    for reel in reels[:10]:
        col1, col2 = st.columns([1, 3])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            st.markdown(f"**{reel.get('hook', '—')}** {badge} `{score}`")
            st.caption(
                f"@{reel['competitor_handle']} · {reel.get('theme', '—')} · "
                f"{reel.get('hook_type', '—')} · "
                f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,}"
            )
            if reel.get("ai_why"):
                st.markdown(f"*Waarom werkt dit: {reel['ai_why']}*")
            if reel.get("ai_your_version"):
                st.success(f"💡 Jouw versie: {reel['ai_your_version']}")
            if reel.get("video_url"):
                st.markdown(f"[🔗 Bekijk Reel]({reel['video_url']})")
        st.divider()

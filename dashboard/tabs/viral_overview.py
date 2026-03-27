# dashboard/tabs/viral_overview.py
import streamlit as st
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal


def render(week, min_score):
    st.subheader("Top Viral Reels Deze Week")
    st.caption(f"Week van {week} · Alle concurrenten · Drempel: viral score ≥ {min_score}")

    reels = get_reels(week=week, min_score=min_score, competitors_only=True)

    if not reels:
        st.info("Geen data gevonden voor deze week. Draai de scraper eerst via GitHub Actions → Run workflow.")
        return

    for reel in reels[:20]:
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=120)
        with col2:
            score = reel.get("viral_score", 0)
            badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
            hook = reel.get("hook", "—")
            st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
            st.caption(f"@{reel['competitor_handle']} · {reel.get('theme', '—')} · {reel.get('hook_type', '—')}")
        with col3:
            if st.button("🔍 Bekijk", key=f"vo_{reel['reel_id']}"):
                show_reel_modal(reel)
        st.divider()

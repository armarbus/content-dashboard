# dashboard/tabs/my_performance.py
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard.queries import get_reels


def render(week):
    st.subheader("Mijn Performance — @aymanraoul")

    my_reels = get_reels(own_only=True)
    my_week_reels = get_reels(week=week, own_only=True)
    competitor_reels = get_reels(week=week, competitors_only=True)

    if not my_reels:
        st.info("Nog geen data voor @aymanraoul. Zorg dat de scraper gedraaid heeft.")
        return

    col1, col2, col3 = st.columns(3)
    my_avg = sum(r["viral_score"] for r in my_week_reels) / max(len(my_week_reels), 1)
    comp_avg = sum(r["viral_score"] for r in competitor_reels) / max(len(competitor_reels), 1)
    diff = my_avg - comp_avg

    with col1:
        st.metric("Jouw gem. score", f"{my_avg:.0f}")
    with col2:
        st.metric("Concurrentie gem.", f"{comp_avg:.0f}")
    with col3:
        st.metric("Verschil", f"{diff:+.0f}")

    if len(my_reels) >= 2:
        df = pd.DataFrame(my_reels)
        df["posted_at"] = pd.to_datetime(df["posted_at"], errors="coerce")
        df = df.dropna(subset=["posted_at"]).sort_values("posted_at")
        fig = px.line(
            df, x="posted_at", y="viral_score",
            title="Viral Score Over Tijd",
            labels={"posted_at": "Datum", "viral_score": "Viral Score"},
        )
        fig.update_traces(line_color="#4ade80")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info("Geen eigen Reels gescraped voor deze week.")
    else:
        for reel in my_week_reels:
            col1, col2 = st.columns([1, 3])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=100)
            with col2:
                score = reel.get("viral_score", 0)
                badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                st.markdown(f"**{reel.get('hook', '—')}** {badge} `{score}`")
                st.caption(
                    f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,} · "
                    f"💬 {reel.get('comments', 0):,} · {str(reel.get('posted_at', ''))[:10]}"
                )
                if reel.get("video_url"):
                    st.markdown(f"[🔗 Bekijk]({reel['video_url']})")
            st.divider()

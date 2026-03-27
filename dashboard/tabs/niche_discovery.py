# dashboard/tabs/niche_discovery.py
import streamlit as st
from dashboard.queries import get_niche_reels
from dashboard.components.reel_modal import show_reel_modal


def render(week, min_score):
    st.subheader("Niche Discovery")

    reels = get_niche_reels(week=week, min_score=min_score)

    if not reels:
        st.info("Nog geen hashtag-reels voor deze week. Ze worden toegevoegd bij de volgende wekelijkse scrape.")
        return

    tags = sorted(set(r.get("niche_tag", "#onbekend") for r in reels))
    for tag in tags:
        tag_reels = [r for r in reels if r.get("niche_tag") == tag]
        st.markdown(f"### Viral in {tag} deze week")
        st.caption(f"{len(tag_reels)} reels gevonden · min score {min_score}")

        for reel in tag_reels:
            col1, col2, col3 = st.columns([1, 6, 1])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=120)
            with col2:
                score = reel.get("viral_score", 0)
                badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                hook = reel.get("hook", "—")
                st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
                st.caption(f"@{reel.get('competitor_handle', '—')} · {reel.get('theme', '—')} · {reel.get('hook_type', '—')}")
            with col3:
                if st.button("🔍 Bekijk", key=f"nd_{reel['reel_id']}"):
                    show_reel_modal(reel)
            st.divider()

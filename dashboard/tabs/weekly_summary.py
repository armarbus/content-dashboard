# dashboard/tabs/weekly_summary.py
import streamlit as st
from dashboard.queries import get_summary, get_available_weeks


def render(week):
    st.subheader("Weekly Summary")

    summary = get_summary(week)

    if not summary:
        weeks = get_available_weeks()
        if len(weeks) > 1:
            prev_week = weeks[1]
            summary = get_summary(prev_week)
            if summary:
                st.info(f"Samenvatting van week {week} nog niet beschikbaar. Vorige week ({prev_week}) getoond.")
            else:
                st.info("Nog geen samenvatting. Wordt aangemaakt na de volgende scrape run.")
                return
        else:
            st.info("Nog geen samenvatting. Wordt aangemaakt na de volgende scrape run.")
            return

    st.markdown("### Trending Thema's")
    st.markdown(summary.get("trending_themes", "—"))

    st.markdown("### Beste Hook-types")
    st.markdown(summary.get("best_hook_types", "—"))

    st.markdown("### Top 3 Om Na Te Maken")
    st.markdown(summary.get("top3_to_copy", "—"))

    st.markdown("### Jouw Contentadvies Deze Week")
    st.success(summary.get("weekly_advice", "—"))

    st.caption(f"Gegenereerd op {str(summary.get('generated_at', ''))[:10]}")

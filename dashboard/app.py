# dashboard/app.py
import streamlit as st
from dashboard.queries import get_available_weeks
from dashboard.tabs import viral_overview, competitor_breakdown, hook_library, value_content, my_performance, weekly_summary

st.set_page_config(
    page_title="Content Dashboard — Ayman",
    page_icon="🔥",
    layout="wide",
)

st.title("🔥 Content Research Dashboard")
st.caption("Hybrid Performance · @aymanraoul")

st.sidebar.header("Filters")

weeks = get_available_weeks()
if not weeks:
    st.warning("Geen data gevonden. Voer eerst de scraper uit via GitHub Actions → Run workflow.")
    st.stop()

selected_week = st.sidebar.selectbox("Week", weeks, index=0)
min_score = st.sidebar.slider("Minimale Viral Score", 0, 100, 60)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔥 Viral Content",
    "👥 Per Concurrent",
    "🪝 Hook Library",
    "💡 Value Content",
    "📈 Mijn Performance",
    "📋 Weekly Summary",
])

with tab1:
    viral_overview.render(selected_week, min_score)
with tab2:
    competitor_breakdown.render(selected_week, min_score)
with tab3:
    hook_library.render(selected_week)
with tab4:
    value_content.render(selected_week)
with tab5:
    my_performance.render(selected_week)
with tab6:
    weekly_summary.render(selected_week)

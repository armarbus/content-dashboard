# dashboard/app.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dashboard.styles import GLOBAL_CSS
from dashboard.queries import get_available_weeks
from dashboard.tabs import (
    viral_overview, niche_discovery, competitor_breakdown,
    hook_library, value_content, my_performance, weekly_summary,
)

st.set_page_config(
    page_title="Content Dashboard — Ayman",
    page_icon="🔥",
    layout="wide",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:4px">
    <h1 style="font-size:30px;font-weight:800;letter-spacing:-0.8px;margin:0;line-height:1.2">
        🔥 Content Research Dashboard
    </h1>
    <p style="color:#6b7280;font-size:12px;margin:4px 0 0 2px;letter-spacing:1px;
       text-transform:uppercase;font-weight:500">
        Hybrid Performance &nbsp;·&nbsp; @aymanraoul &nbsp;·&nbsp; @ronencaspers
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<p style="font-size:10px;font-weight:700;letter-spacing:2px;text-transform:uppercase;
   color:#6b7280;margin-bottom:16px">Filters</p>
""", unsafe_allow_html=True)

weeks = get_available_weeks()
if not weeks:
    st.warning("Geen data gevonden. Voer eerst de scraper uit via GitHub Actions → Run workflow.")
    st.stop()

selected_week = st.sidebar.selectbox("Week", weeks, index=0)
min_score = st.sidebar.slider("Minimale Viral Score", 0, 100, 60)

st.sidebar.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:16px 0'>", unsafe_allow_html=True)
st.sidebar.markdown("""
<p style="font-size:10px;color:#4b5563;letter-spacing:0.5px">
    Data ververst wekelijks via GitHub Actions.<br>
    Scraper: apify/instagram-scraper
</p>
""", unsafe_allow_html=True)

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔥 Viral Content",
    "🔍 Niche Discovery",
    "👥 Per Concurrent",
    "🪝 Hook Library",
    "💡 Value Content",
    "📈 Mijn Performance",
    "📋 Weekly Summary",
])

with tab1:
    viral_overview.render(selected_week, min_score)
with tab2:
    niche_discovery.render(selected_week, min_score)
with tab3:
    competitor_breakdown.render(selected_week, min_score)
with tab4:
    hook_library.render(selected_week)
with tab5:
    value_content.render(selected_week)
with tab6:
    my_performance.render(selected_week)
with tab7:
    weekly_summary.render(selected_week)

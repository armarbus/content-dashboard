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
    page_title="Back 2 Work — Content Dashboard",
    page_icon="🔥",
    layout="wide",
)

st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #1E1E1E">
    <span style="font-family:'Anton',sans-serif;font-size:26px;font-weight:400;
        text-transform:uppercase;letter-spacing:0.06em;color:#F5F5F5;
        line-height:1">BACK 2 WORK</span>
    <div style="display:flex;align-items:center;gap:10px;margin-top:8px">
        <span style="width:20px;height:2px;background:#E9003A;display:inline-block;flex-shrink:0"></span>
        <span style="color:#B7B7B7;font-size:10px;font-weight:700;letter-spacing:2px;
              text-transform:uppercase;font-family:Inter,sans-serif">
            Content Research Dashboard
        </span>
        <span style="width:20px;height:2px;background:#E9003A;display:inline-block;flex-shrink:0"></span>
        <span style="color:#B7B7B7;font-size:10px;letter-spacing:1px;font-family:Roboto Mono,monospace">
            @aymanraoul · @ronencaspers
        </span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<p style="font-family:Inter,sans-serif;font-size:9px;font-weight:700;
   letter-spacing:2.5px;text-transform:uppercase;color:#B7B7B7;margin-bottom:16px">
   Filters
</p>
""", unsafe_allow_html=True)

weeks = get_available_weeks()
if not weeks:
    st.warning("Geen data gevonden. Voer eerst de scraper uit via GitHub Actions → Run workflow.")
    st.stop()

selected_week = st.sidebar.selectbox("Week", weeks, index=0)
min_score = st.sidebar.slider("Minimale Viral Score", 0, 100, 60)

st.sidebar.markdown("""
<div style="margin-top:24px;padding-top:16px;border-top:1px solid #1E1E1E">
    <p style="font-family:Roboto Mono,monospace;font-size:10px;color:#B7B7B7;
       letter-spacing:0.3px;margin:0">Data refresht wekelijks</p>
    <p style="font-family:Roboto Mono,monospace;font-size:10px;color:#2a2a2a;
       letter-spacing:0.3px;margin:4px 0 0 0">apify/instagram-scraper</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────────
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

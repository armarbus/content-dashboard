# dashboard/styles.py
"""Global CSS injected once in app.py via st.markdown(GLOBAL_CSS, unsafe_allow_html=True)."""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Sidebar ─────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0d0d0d !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] h2 {
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    color: #6b7280 !important;
}

/* ── Tabs ────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 3px;
    background: rgba(255,255,255,0.03);
    padding: 5px;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.07);
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #9ca3af !important;
    padding: 5px 13px !important;
    border-bottom: none !important;
    background: transparent !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,255,255,0.09) !important;
    color: #f9fafb !important;
}

/* ── Metric cards ────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px 24px;
}
[data-testid="stMetricLabel"] p {
    font-size: 11px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    color: #6b7280 !important;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 800 !important;
}

/* ── Reel cards (bordered containers) ────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    margin-bottom: 8px !important;
    transition: border-color 0.2s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(255,255,255,0.18) !important;
}

/* ── Buttons ─────────────────────────────────── */
[data-testid="stButton"] > button {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%) !important;
    border: none !important;
    font-weight: 600 !important;
}

/* ── Dividers ────────────────────────────────── */
hr {
    border-color: rgba(255,255,255,0.06) !important;
    margin: 4px 0 !important;
}

/* ── Dataframe ───────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Expander ────────────────────────────────── */
[data-testid="stExpander"] {
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
}

/* ── Alerts ──────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
}

/* ── Typography ──────────────────────────────── */
h1 { font-weight: 800 !important; letter-spacing: -0.5px !important; }
h2 { font-weight: 700 !important; letter-spacing: -0.3px !important; }
h3 { font-weight: 600 !important; }

/* ── Form controls ───────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    border-radius: 8px !important;
}

/* ── Scrollbar ───────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }
</style>
"""

# dashboard/styles.py
"""
Global CSS — Back 2 Work Brand Guidelines.
Colors: #0A0A0A black, #F5F5F5 white, #E9003A red, #1E1E1E steel grey,
        #B7B7B7 silver, #00C27A success green.
Fonts: Anton (headings), Inter (body), Roboto Mono (KPIs/numbers).
Border radius: max 4px.
"""

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500;600;700&display=swap');

/* ── Base ───────────────────────────────────────────────────────────── */
*, *::before, *::after {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Sidebar ────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0A0A0A !important;
    border-right: 1px solid #1E1E1E !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: #1E1E1E;
    padding: 4px;
    border-radius: 4px;
    border: 1px solid #2a2a2a;
    flex-wrap: wrap;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 2px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    color: #B7B7B7 !important;
    padding: 6px 14px !important;
    border-bottom: none !important;
    background: transparent !important;
    font-family: 'Inter', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: #E9003A !important;
    color: #F5F5F5 !important;
}

/* ── Metric cards ───────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: #1E1E1E;
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    padding: 20px 24px;
}
[data-testid="stMetricLabel"] p {
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    color: #B7B7B7 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 32px !important;
    font-weight: 600 !important;
    color: #F5F5F5 !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'Roboto Mono', monospace !important;
    font-size: 13px !important;
}

/* ── Reel cards (bordered containers) ──────────────────────────────── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 4px !important;
    border: 1px solid #1E1E1E !important;
    background: #0d0d0d !important;
    margin-bottom: 6px !important;
    transition: border-color 0.15s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #E9003A !important;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
[data-testid="stButton"] > button {
    border-radius: 4px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    text-transform: uppercase !important;
    font-family: 'Inter', sans-serif !important;
    padding: 8px 16px !important;
    transition: all 0.15s ease !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: #E9003A !important;
    border: 1px solid #E9003A !important;
    color: #F5F5F5 !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    background: #c4002f !important;
    border-color: #c4002f !important;
}
[data-testid="stButton"] > button:not([kind="primary"]) {
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    color: #B7B7B7 !important;
}
[data-testid="stButton"] > button:not([kind="primary"]):hover {
    border-color: #E9003A !important;
    color: #E9003A !important;
}

/* ── Dividers ───────────────────────────────────────────────────────── */
hr {
    border-color: #1E1E1E !important;
    margin: 4px 0 !important;
}

/* ── Dataframe ──────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 4px;
    border: 1px solid #1E1E1E !important;
}

/* ── Expander ───────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    border-radius: 4px !important;
    border: 1px solid #1E1E1E !important;
    background: #0d0d0d !important;
}

/* ── Alerts ─────────────────────────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 4px !important;
}
div[data-testid="stAlert"][kind="success"],
div[class*="stSuccess"] {
    border-left: 3px solid #00C27A !important;
    background: rgba(0,194,122,0.06) !important;
}
div[data-testid="stAlert"][kind="warning"],
div[class*="stWarning"] {
    border-left: 3px solid #E9003A !important;
    background: rgba(233,0,58,0.06) !important;
}
div[data-testid="stAlert"][kind="info"],
div[class*="stInfo"] {
    border-left: 3px solid #B7B7B7 !important;
    background: rgba(183,183,183,0.04) !important;
}

/* ── Typography ─────────────────────────────────────────────────────── */
h1 {
    font-family: 'Anton', sans-serif !important;
    font-weight: 400 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: #F5F5F5 !important;
}
h2 {
    font-family: 'Anton', sans-serif !important;
    font-weight: 400 !important;
    letter-spacing: 0.03em !important;
    color: #F5F5F5 !important;
}
h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: #F5F5F5 !important;
    letter-spacing: 0.01em !important;
}

/* ── Form controls ──────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    border-radius: 4px !important;
    background: #1E1E1E !important;
    border-color: #2a2a2a !important;
}

/* ── Slider ─────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #E9003A !important;
    border-color: #E9003A !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [data-testid="stThumbValue"] {
    color: #E9003A !important;
}

/* ── Radio buttons ──────────────────────────────────────────────────── */
[data-testid="stRadio"] label {
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: #B7B7B7 !important;
}

/* ── Caption ────────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    color: #B7B7B7 !important;
    font-size: 11px !important;
    letter-spacing: 0.3px !important;
}

/* ── Scrollbar ──────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: #0A0A0A; }
::-webkit-scrollbar-thumb { background: #1E1E1E; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #E9003A; }
</style>
"""

# dashboard/tabs/my_performance.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card

MIN_SAMPLE = 3

# Brand colors
OWN_COLOR = "#E9003A"       # Hybrid Red — own bars
OWN_WEAK_COLOR = "#2a2a2a"  # steel — too little data
COMP_COLOR = "#1E1E1E"      # steel grey — competitor bars
GRID_COLOR = "rgba(30,30,30,0.8)"
TEXT_COLOR = "#B7B7B7"

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_COLOR, tickfont=dict(family="Roboto Mono")),
    xaxis=dict(color=TEXT_COLOR, tickfont=dict(family="Inter", size=11)),
    margin=dict(l=0, r=0, t=36, b=0),
    font=dict(family="Inter, sans-serif", color=TEXT_COLOR),
)


def _grouped_bar_chart(my_df: pd.DataFrame, comp_df: pd.DataFrame, group_col: str, title: str):
    my_agg = my_df.groupby(group_col)["viral_score"].agg(["mean", "count"]).reset_index()
    my_agg.columns = [group_col, "my_avg", "my_count"]
    comp_agg = comp_df.groupby(group_col)["viral_score"].mean().reset_index()
    comp_agg.columns = [group_col, "comp_avg"]
    merged = my_agg.merge(comp_agg, on=group_col, how="outer").fillna(0)

    fig = go.Figure()
    for _, row in merged.iterrows():
        label = row[group_col]
        has_data = row["my_count"] >= MIN_SAMPLE
        fig.add_trace(go.Bar(
            name=f"Jij ({label})", x=[label], y=[row["my_avg"]],
            marker_color=OWN_COLOR if has_data else OWN_WEAK_COLOR,
            marker_line_color=OWN_COLOR if has_data else "#374151",
            marker_line_width=1,
            showlegend=False,
            text=[f"n={int(row['my_count'])}"] if not has_data and row["my_count"] > 0 else None,
            textposition="inside",
            textfont=dict(family="Roboto Mono", size=10),
        ))
        fig.add_trace(go.Bar(
            name=f"Concurrenten ({label})", x=[label], y=[row["comp_avg"]],
            marker_color=COMP_COLOR,
            marker_line_color="#374151",
            marker_line_width=1,
            showlegend=False,
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter", size=13, color=TEXT_COLOR)),
        barmode="group",
        **CHART_LAYOUT,
    )
    return fig, merged


def render(week):
    st.subheader("Mijn Performance")

    # ── Account selector ──────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:12px">
        <span style="font-size:10px;font-weight:700;letter-spacing:2px;
              text-transform:uppercase;color:#B7B7B7;font-family:Inter,sans-serif">
            Account
        </span>
    </div>
    """, unsafe_allow_html=True)

    account_choice = st.radio(
        "Account",
        ["@aymanraoul", "@ronencaspers"],
        horizontal=True,
        label_visibility="collapsed",
    )
    handle = account_choice.lstrip("@")

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    st.markdown(f"<div style='height:2px;width:32px;background:#E9003A;margin-bottom:16px'></div>", unsafe_allow_html=True)

    # ── Fetch data ────────────────────────────────────────────────────
    if handle == "aymanraoul":
        my_reels = get_reels(own_only=True)
        my_week_reels = get_reels(week=week, own_only=True)
    else:
        my_reels = get_reels(handles=[handle])
        my_week_reels = get_reels(week=week, handles=[handle])

    # Competitors = everyone except selected account
    all_week = get_reels(week=week)
    competitor_reels = [
        r for r in all_week
        if r.get("competitor_handle") != handle and not (handle == "aymanraoul" and r.get("is_own_account"))
    ]

    if not my_reels:
        st.info(f"Nog geen data voor @{handle}. Zorg dat de scraper gedraaid heeft.")
        return

    # ── KPI helpers ───────────────────────────────────────────────────
    def _eng_rate(reels):
        rates = [
            (r.get("likes", 0) + r.get("comments", 0)) / r["views"] * 100
            for r in reels if r.get("views", 0) > 0
        ]
        return sum(rates) / len(rates) if rates else 0.0

    my_avg = sum(r["viral_score"] for r in my_week_reels) / max(len(my_week_reels), 1)
    comp_avg = sum(r["viral_score"] for r in competitor_reels) / max(len(competitor_reels), 1)
    diff = my_avg - comp_avg
    my_avg_views = sum(r.get("views", 0) for r in my_week_reels) / max(len(my_week_reels), 1)
    my_eng = _eng_rate(my_week_reels)
    comp_eng = _eng_rate(competitor_reels)

    # ── KPI cards — row 1: viral score ────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("GEM. VIRAL SCORE", f"{my_avg:.0f}")
    col2.metric("CONCURRENTIE GEM.", f"{comp_avg:.0f}")
    col3.metric("VERSCHIL", f"{diff:+.0f}")

    # ── KPI cards — row 2: views + engagement ────────────────────────
    col4, col5, col6 = st.columns(3)
    col4.metric("GEM. VIEWS", f"{my_avg_views:,.0f}")
    col5.metric("ENGAGEMENT %", f"{my_eng:.2f}%")
    col6.metric("COMP. ENGAGEMENT %", f"{comp_eng:.2f}%",
                delta=f"{my_eng - comp_eng:+.2f}%",
                delta_color="normal")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Trend charts ──────────────────────────────────────────────────
    if len(my_reels) >= 2:
        df_all = pd.DataFrame(my_reels)
        df_all["posted_at"] = pd.to_datetime(df_all["posted_at"], errors="coerce")
        df_all = df_all.dropna(subset=["posted_at"]).sort_values("posted_at")
        df_all["engagement_pct"] = df_all.apply(
            lambda r: (r.get("likes", 0) + r.get("comments", 0)) / r["views"] * 100
            if r.get("views", 0) > 0 else 0,
            axis=1,
        )

        tcol1, tcol2 = st.columns(2)
        with tcol1:
            fig_score = px.line(
                df_all, x="posted_at", y="viral_score",
                title="VIRAL SCORE OVER TIJD",
                labels={"posted_at": "", "viral_score": "Score"},
            )
            fig_score.update_traces(line_color=OWN_COLOR, line_width=2)
            fig_score.update_layout(
                title=dict(font=dict(family="Anton", size=13, color=TEXT_COLOR)),
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_score, use_container_width=True)

        with tcol2:
            fig_views = px.line(
                df_all, x="posted_at", y="views",
                title="VIEWS OVER TIJD",
                labels={"posted_at": "", "views": "Views"},
            )
            fig_views.update_traces(line_color="#00C27A", line_width=2)
            fig_views.update_layout(
                title=dict(font=dict(family="Anton", size=13, color=TEXT_COLOR)),
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig_views, use_container_width=True)

    # ── Hook & Theme breakdown ────────────────────────────────────────
    if my_reels and competitor_reels:
        my_df = pd.DataFrame(my_reels)
        comp_df = pd.DataFrame(competitor_reels)

        st.markdown("### Hook Type Breakdown")
        fig_hook, hook_merged = _grouped_bar_chart(
            my_df, comp_df, "hook_type", "HOOK TYPE — JIJ VS CONCURRENTEN"
        )
        st.plotly_chart(fig_hook, use_container_width=True)

        qualified = hook_merged[hook_merged["my_count"] >= MIN_SAMPLE].copy()
        if not qualified.empty:
            qualified["diff"] = qualified["my_avg"] - qualified["comp_avg"]
            best = qualified.loc[qualified["diff"].idxmax()]
            st.success(
                f"✅ **{best['hook_type'].upper()}** scoort {best['diff']:.0f}pt boven concurrentie — post er meer van"
            )

        st.markdown("### Thema Breakdown")
        fig_theme, theme_merged = _grouped_bar_chart(
            my_df, comp_df, "theme", "THEMA — JIJ VS CONCURRENTEN"
        )
        st.plotly_chart(fig_theme, use_container_width=True)

        qualified_theme = theme_merged[theme_merged["my_count"] >= MIN_SAMPLE].copy()
        if not qualified_theme.empty:
            worst = qualified_theme.loc[qualified_theme["my_avg"].idxmin()]
            st.warning(
                f"⚠️ **{worst['theme'].upper()}** scoort zwak (gem. {worst['my_avg']:.0f}) — test een andere aanpak"
            )

    # ── Content Goals ─────────────────────────────────────────────────
    st.markdown("### Content Goals")
    avg_views_k = my_avg_views / 1000
    goals = [
        ("Viral Score",        my_avg,           75,    f"{my_avg:.0f} / 75"),
        ("Reels Deze Week",    len(my_week_reels), 5,   f"{len(my_week_reels)} / 5"),
        ("Avg Views",          avg_views_k,       50,   f"{avg_views_k:.0f}k / 50k"),
        ("Engagement %",       my_eng,            3.0,  f"{my_eng:.2f}% / 3%"),
    ]
    gcols = st.columns(4)
    for col, (label, val, target, display) in zip(gcols, goals):
        pct = min(val / max(target, 1), 1.0)
        bar_color = "#00C27A" if pct >= 1.0 else "#E9003A" if pct >= 0.6 else "#B7B7B7"
        with col:
            st.markdown(
                f'<div style="background:#1E1E1E;border:1px solid #2a2a2a;border-radius:4px;padding:14px 16px">'
                f'<p style="font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;'
                f'color:#B7B7B7;font-family:Inter,sans-serif;margin:0 0 6px 0">{label}</p>'
                f'<p style="font-family:Roboto Mono,monospace;font-size:20px;font-weight:600;'
                f'color:#F5F5F5;margin:0 0 10px 0">{display}</p>'
                f'<div style="background:#2a2a2a;border-radius:2px;height:4px">'
                f'<div style="background:{bar_color};width:{pct*100:.0f}%;height:4px;border-radius:2px;'
                f'transition:width 0.3s ease"></div></div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Weekly reels ──────────────────────────────────────────────────
    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info(f"Geen Reels gescraped voor @{handle} deze week.")
    else:
        for reel in my_week_reels:
            render_reel_card(reel, button_key=f"mp_{reel['reel_id']}")

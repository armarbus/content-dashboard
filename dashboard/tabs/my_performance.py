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

    # ── KPI cards ─────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    my_avg = sum(r["viral_score"] for r in my_week_reels) / max(len(my_week_reels), 1)
    comp_avg = sum(r["viral_score"] for r in competitor_reels) / max(len(competitor_reels), 1)
    diff = my_avg - comp_avg
    with col1:
        st.metric("GEM. VIRAL SCORE", f"{my_avg:.0f}")
    with col2:
        st.metric("CONCURRENTIE GEM.", f"{comp_avg:.0f}")
    with col3:
        st.metric("VERSCHIL", f"{diff:+.0f}")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Trend chart ───────────────────────────────────────────────────
    if len(my_reels) >= 2:
        df_all = pd.DataFrame(my_reels)
        df_all["posted_at"] = pd.to_datetime(df_all["posted_at"], errors="coerce")
        df_all = df_all.dropna(subset=["posted_at"]).sort_values("posted_at")
        fig = px.line(
            df_all, x="posted_at", y="viral_score",
            title="VIRAL SCORE OVER TIJD",
            labels={"posted_at": "Datum", "viral_score": "Viral Score"},
        )
        fig.update_traces(line_color=OWN_COLOR, line_width=2)
        fig.update_layout(
            title=dict(font=dict(family="Anton", size=14, color=TEXT_COLOR)),
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

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

    # ── Weekly reels ──────────────────────────────────────────────────
    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info(f"Geen Reels gescraped voor @{handle} deze week.")
    else:
        for reel in my_week_reels:
            render_reel_card(reel, button_key=f"mp_{reel['reel_id']}")

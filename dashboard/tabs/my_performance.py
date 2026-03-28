# dashboard/tabs/my_performance.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card

MIN_SAMPLE = 3


def _grouped_bar_chart(my_df: pd.DataFrame, comp_df: pd.DataFrame, group_col: str, title: str):
    """Returns a Plotly figure comparing avg viral score for Ayman vs competitors per group."""
    my_agg = my_df.groupby(group_col)["viral_score"].agg(["mean", "count"]).reset_index()
    my_agg.columns = [group_col, "my_avg", "my_count"]

    comp_agg = comp_df.groupby(group_col)["viral_score"].mean().reset_index()
    comp_agg.columns = [group_col, "comp_avg"]

    merged = my_agg.merge(comp_agg, on=group_col, how="outer").fillna(0)

    fig = go.Figure()
    for _, row in merged.iterrows():
        label = row[group_col]
        my_color = "#4ade80" if row["my_count"] >= MIN_SAMPLE else "#374151"
        fig.add_trace(go.Bar(
            name=f"Jij ({label})", x=[label], y=[row["my_avg"]],
            marker_color=my_color, showlegend=False,
            text=[f"n={int(row['my_count'])}"] if row["my_count"] < MIN_SAMPLE and row["my_count"] > 0 else None,
            textposition="inside",
        ))
        fig.add_trace(go.Bar(
            name=f"Concurrenten ({label})", x=[label], y=[row["comp_avg"]],
            marker_color="#374151", showlegend=False,
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#9ca3af")),
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Gem. Viral Score",
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#6b7280"),
        xaxis=dict(color="#9ca3af"),
        margin=dict(l=0, r=0, t=40, b=0),
        font=dict(family="Inter, sans-serif"),
    )
    return fig, merged


def render(week):
    st.subheader("Mijn Performance — @aymanraoul")

    my_reels = get_reels(own_only=True)
    my_week_reels = get_reels(week=week, own_only=True)
    competitor_reels = get_reels(week=week, competitors_only=True)

    if not my_reels:
        st.info("Nog geen data voor @aymanraoul. Zorg dat de scraper gedraaid heeft.")
        return

    # KPI cards
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

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Trend chart
    if len(my_reels) >= 2:
        df_all = pd.DataFrame(my_reels)
        df_all["posted_at"] = pd.to_datetime(df_all["posted_at"], errors="coerce")
        df_all = df_all.dropna(subset=["posted_at"]).sort_values("posted_at")
        fig = px.line(
            df_all, x="posted_at", y="viral_score",
            title="Viral Score Over Tijd",
            labels={"posted_at": "Datum", "viral_score": "Viral Score"},
        )
        fig.update_traces(line_color="#4ade80", line_width=2)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            title=dict(font=dict(size=14, color="#9ca3af")),
            yaxis=dict(gridcolor="rgba(255,255,255,0.06)", color="#6b7280"),
            xaxis=dict(color="#9ca3af"),
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(family="Inter, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # Hook & Theme breakdown
    if my_reels and competitor_reels:
        my_df = pd.DataFrame(my_reels)
        comp_df = pd.DataFrame(competitor_reels)

        st.markdown("### Hook Type Breakdown")
        fig_hook, hook_merged = _grouped_bar_chart(my_df, comp_df, "hook_type", "Jij vs Concurrenten per Hook Type")
        st.plotly_chart(fig_hook, use_container_width=True)

        qualified = hook_merged[hook_merged["my_count"] >= MIN_SAMPLE].copy()
        if not qualified.empty:
            qualified["diff"] = qualified["my_avg"] - qualified["comp_avg"]
            best = qualified.loc[qualified["diff"].idxmax()]
            st.success(f"✅ Je scoort **{best['diff']:.0f}pt** beter op **{best['hook_type']}** hooks → post er meer van")

        st.markdown("### Thema Breakdown")
        fig_theme, theme_merged = _grouped_bar_chart(my_df, comp_df, "theme", "Jij vs Concurrenten per Thema")
        st.plotly_chart(fig_theme, use_container_width=True)

        qualified_theme = theme_merged[theme_merged["my_count"] >= MIN_SAMPLE].copy()
        if not qualified_theme.empty:
            worst = qualified_theme.loc[qualified_theme["my_avg"].idxmin()]
            st.warning(f"⚠️ Je **{worst['theme']}** content scoort zwak (gem. {worst['my_avg']:.0f}) → test een andere aanpak")

    # Weekly reels
    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info("Geen eigen Reels gescraped voor deze week.")
    else:
        for reel in my_week_reels:
            render_reel_card(reel, button_key=f"mp_{reel['reel_id']}")

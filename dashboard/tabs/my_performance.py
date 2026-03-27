# dashboard/tabs/my_performance.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.queries import get_reels
from dashboard.components.reel_modal import show_reel_modal

MIN_SAMPLE = 3  # minimum own-reel count per hook_type/theme to show bar


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
        if row["my_count"] >= MIN_SAMPLE:
            fig.add_trace(go.Bar(
                name=f"Jij ({label})",
                x=[label], y=[row["my_avg"]],
                marker_color="#4ade80",
                showlegend=False,
            ))
        else:
            fig.add_trace(go.Bar(
                name=f"Jij ({label})",
                x=[label], y=[row["my_avg"] if row["my_count"] > 0 else 0],
                marker_color="#374151",
                text=[f"te weinig data (n={int(row['my_count'])})"],
                textposition="inside",
                showlegend=False,
            ))
        fig.add_trace(go.Bar(
            name=f"Concurrenten ({label})",
            x=[label], y=[row["comp_avg"]],
            marker_color="#6b7280",
            showlegend=False,
        ))

    fig.update_layout(
        title=title,
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Gem. Viral Score",
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

    # Section 1 — KPI cards
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

    # Trend chart (all time)
    if len(my_reels) >= 2:
        df_all = pd.DataFrame(my_reels)
        df_all["posted_at"] = pd.to_datetime(df_all["posted_at"], errors="coerce")
        df_all = df_all.dropna(subset=["posted_at"]).sort_values("posted_at")
        fig = px.line(
            df_all, x="posted_at", y="viral_score",
            title="Viral Score Over Tijd",
            labels={"posted_at": "Datum", "viral_score": "Viral Score"},
        )
        fig.update_traces(line_color="#4ade80")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Section 2 — Hook type breakdown
    if my_reels and competitor_reels:
        st.markdown("### Hook Type Breakdown")
        my_df = pd.DataFrame(my_reels)
        comp_df = pd.DataFrame(competitor_reels)

        fig_hook, hook_merged = _grouped_bar_chart(my_df, comp_df, "hook_type", "Jij vs Concurrenten per Hook Type")
        st.plotly_chart(fig_hook, use_container_width=True)

        qualified = hook_merged[hook_merged["my_count"] >= MIN_SAMPLE].copy()
        if not qualified.empty:
            qualified["diff"] = qualified["my_avg"] - qualified["comp_avg"]
            best = qualified.loc[qualified["diff"].idxmax()]
            st.success(f"✅ Je scoort **{best['diff']:.0f}pt** beter op **{best['hook_type']}** hooks → post er meer van")

        # Section 3 — Theme breakdown
        st.markdown("### Thema Breakdown")
        fig_theme, theme_merged = _grouped_bar_chart(my_df, comp_df, "theme", "Jij vs Concurrenten per Thema")
        st.plotly_chart(fig_theme, use_container_width=True)

        qualified_theme = theme_merged[theme_merged["my_count"] >= MIN_SAMPLE].copy()
        if not qualified_theme.empty:
            worst = qualified_theme.loc[qualified_theme["my_avg"].idxmin()]
            st.warning(f"⚠️ Je **{worst['theme']}** content scoort zwak (gem. {worst['my_avg']:.0f}) → test een andere aanpak")

    # Section 4 — Weekly reels
    st.markdown("### Deze Week")
    if not my_week_reels:
        st.info("Geen eigen Reels gescraped voor deze week.")
    else:
        for reel in my_week_reels:
            col1, col2, col3 = st.columns([1, 6, 1])
            with col1:
                if reel.get("thumbnail_url"):
                    st.image(reel["thumbnail_url"], width=120)
            with col2:
                score = reel.get("viral_score", 0)
                badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"
                hook = reel.get("hook", "—")
                st.markdown(f"**{hook[:80]}{'…' if len(hook) > 80 else ''}** {badge} `{score}`")
                st.caption(
                    f"👁 {reel.get('views', 0):,} · ❤️ {reel.get('likes', 0):,} · "
                    f"💬 {reel.get('comments', 0):,} · {str(reel.get('posted_at', ''))[:10]}"
                )
            with col3:
                if st.button("🔍 Bekijk", key=f"mp_{reel['reel_id']}"):
                    show_reel_modal(reel)
            st.divider()

# dashboard/tabs/hook_library.py
import streamlit as st
import pandas as pd
from dashboard.queries import get_reels
from dashboard.components.reel_card import render_reel_card

HOOK_TYPES = ["identiteit", "tegenstelling", "discipline", "transformatie", "lifestyle", "anders"]


def render(week):
    st.subheader("Hook Library")
    st.caption("Hooks gegroepeerd op type · gesorteerd op effectiviteit")

    reels = get_reels(week=week, competitors_only=True)
    if not reels:
        st.info("Geen data voor deze week.")
        return

    selected_type = st.selectbox("Filter op hook-type", ["Alle"] + HOOK_TYPES)
    filtered = reels if selected_type == "Alle" else [r for r in reels if r.get("hook_type") == selected_type]

    df = pd.DataFrame(filtered)
    if df.empty:
        st.info("Geen hooks gevonden.")
        return

    if "hook_type" in df.columns and "viral_score" in df.columns:
        summary = df.groupby("hook_type")["viral_score"].agg(["mean", "count"]).reset_index()
        summary.columns = ["hook_type", "avg", "count"]
        summary = summary.sort_values("avg", ascending=False)
        max_score = summary["avg"].max() or 1
        rows_html = ""
        for _, row in summary.iterrows():
            pct = row["avg"] / max_score * 100
            bar_color = "#00C27A" if row["avg"] >= 70 else "#E9003A" if row["avg"] >= 50 else "#B7B7B7"
            rows_html += (
                f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0;'
                f'border-bottom:1px solid #1E1E1E">'
                f'<span style="font-family:Inter,sans-serif;font-size:12px;color:#F5F5F5;'
                f'width:110px;flex-shrink:0">{row["hook_type"]}</span>'
                f'<div style="flex:1;background:#2a2a2a;border-radius:2px;height:6px">'
                f'<div style="background:{bar_color};width:{pct:.0f}%;height:6px;border-radius:2px"></div></div>'
                f'<span style="font-family:Roboto Mono,monospace;font-size:12px;font-weight:600;'
                f'color:{bar_color};width:40px;text-align:right">{row["avg"]:.0f}</span>'
                f'<span style="font-family:Roboto Mono,monospace;font-size:11px;color:#B7B7B7;'
                f'width:40px;text-align:right">n={int(row["count"])}</span>'
                f'</div>'
            )
        st.markdown(
            f'<div style="background:#1E1E1E;border:1px solid #2a2a2a;border-radius:4px;'
            f'padding:12px 16px;margin-bottom:12px">{rows_html}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for reel in filtered:
        render_reel_card(reel, button_key=f"hl_{reel['reel_id']}")

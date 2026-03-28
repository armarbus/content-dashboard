# dashboard/components/reel_card.py
"""
Shared reel card renderer used across all tabs.
Renders a single reel as a bordered card with score badge + hook + metadata.
"""
import streamlit as st
from dashboard.components.reel_modal import show_reel_modal


def _score_badge(score: int) -> str:
    """Returns an HTML pill badge coloured by score tier."""
    if score >= 70:
        color, bg = "#4ade80", "rgba(74,222,128,0.12)"
    elif score >= 50:
        color, bg = "#fbbf24", "rgba(251,191,36,0.12)"
    else:
        color, bg = "#f87171", "rgba(248,113,113,0.12)"
    return (
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f'padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700;'
        f'border:1px solid {color}28;margin-right:6px;vertical-align:middle">'
        f'{score}</span>'
    )


def _placeholder() -> None:
    """Renders a grey placeholder when thumbnail is missing."""
    st.markdown(
        '<div style="width:110px;height:80px;background:rgba(255,255,255,0.04);'
        'border-radius:8px;display:flex;align-items:center;justify-content:'
        'center;font-size:26px;color:#374151">🎬</div>',
        unsafe_allow_html=True,
    )


def render_reel_card(reel: dict, button_key: str) -> None:
    """
    Renders a single reel row as a bordered card.
    Opens the shared modal on Bekijk click.
    """
    score = reel.get("viral_score", 0)
    hook = reel.get("hook", "—")
    hook_display = f"{hook[:88]}{'…' if len(hook) > 88 else ''}"
    handle = reel.get("competitor_handle", "—")
    theme = reel.get("theme", "—")
    hook_type = reel.get("hook_type", "—")
    views = reel.get("views", 0)

    meta_items = [
        f'<span style="color:#9ca3af">@{handle}</span>',
        f'<span style="color:#6b7280">{theme}</span>',
        f'<span style="color:#6b7280">{hook_type}</span>',
        f'<span style="color:#6b7280">👁 {views:,}</span>',
    ]
    meta_html = ' <span style="color:#374151;margin:0 3px">·</span> '.join(meta_items)

    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            if reel.get("thumbnail_url"):
                st.image(reel["thumbnail_url"], width=110)
            else:
                _placeholder()
        with col2:
            st.markdown(
                f'{_score_badge(score)}'
                f'<span style="font-size:14px;font-weight:600;color:#f1f5f9;'
                f'line-height:1.5;vertical-align:middle">{hook_display}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:12px;margin-top:5px;line-height:1.6">'
                f'{meta_html}</div>',
                unsafe_allow_html=True,
            )
        with col3:
            if st.button("Bekijk", key=button_key, use_container_width=True):
                show_reel_modal(reel)

# dashboard/components/reel_card.py
"""
Shared reel card renderer — Back 2 Work brand guidelines.
Colors: #E9003A red, #00C27A green, #B7B7B7 silver, #1E1E1E steel grey.
"""
import streamlit as st
from dashboard.components.reel_modal import show_reel_modal


def _score_badge(score: int) -> str:
    """Returns a brand-styled score badge. Green ≥70, Red ≥50, Silver <50."""
    if score >= 70:
        color, bg = "#00C27A", "rgba(0,194,122,0.10)"
    elif score >= 50:
        color, bg = "#E9003A", "rgba(233,0,58,0.10)"
    else:
        color, bg = "#B7B7B7", "rgba(183,183,183,0.08)"
    return (
        f'<span style="display:inline-block;background:{bg};color:{color};'
        f'padding:1px 8px;border-radius:2px;font-size:11px;font-weight:700;'
        f'font-family:Roboto Mono,monospace;letter-spacing:0.5px;'
        f'border:1px solid {color}40;margin-right:8px;vertical-align:middle">'
        f'{score}</span>'
    )


def _placeholder() -> None:
    st.markdown(
        '<div style="width:110px;height:80px;background:#1E1E1E;'
        'border:1px solid #2a2a2a;border-radius:2px;'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:18px;color:#B7B7B7;font-family:Roboto Mono,monospace">▶</div>',
        unsafe_allow_html=True,
    )


def render_reel_card(reel: dict, button_key: str) -> None:
    """Renders a single reel row as a brand-styled bordered card."""
    score = reel.get("viral_score", 0)
    hook = reel.get("hook", "—")
    hook_display = f"{hook[:88]}{'…' if len(hook) > 88 else ''}"
    handle = reel.get("competitor_handle", "—")
    theme = reel.get("theme", "—")
    hook_type = reel.get("hook_type", "—")
    views = reel.get("views", 0)

    sep = '<span style="color:#2a2a2a;margin:0 5px">|</span>'
    meta_html = (
        f'<span style="color:#B7B7B7;font-size:11px;font-family:Inter,sans-serif">'
        f'@{handle}{sep}{theme}{sep}{hook_type}'
        f'{sep}<span style="font-family:Roboto Mono,monospace">{views:,}</span> views'
        f'</span>'
    )

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
                f'<span style="font-size:14px;font-weight:600;color:#F5F5F5;'
                f'font-family:Inter,sans-serif;line-height:1.5;vertical-align:middle">'
                f'{hook_display}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="margin-top:4px">{meta_html}</div>',
                unsafe_allow_html=True,
            )
        with col3:
            if st.button("BEKIJK", key=button_key, use_container_width=True):
                show_reel_modal(reel)

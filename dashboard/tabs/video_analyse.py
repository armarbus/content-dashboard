# dashboard/tabs/video_analyse.py
import os
import streamlit as st
from dashboard.components.video_analyzer import download_audio, transcribe, analyze


def render():
    st.subheader("Video Analyse")
    st.caption(
        "Plak een Instagram Reel of YouTube Short URL → automatische download, "
        "Whisper transcriptie en GPT-4o analyse."
    )

    url = st.text_input(
        "Video URL",
        placeholder="https://www.instagram.com/reel/... of https://www.youtube.com/shorts/...",
        key="va_url_input",
    )

    col_btn, col_reset = st.columns([3, 1])
    with col_btn:
        run = st.button("🔬 Analyseer Video", type="primary", use_container_width=True,
                        disabled=not bool(url))
    with col_reset:
        if st.button("↺ Reset", use_container_width=True):
            for k in [k for k in st.session_state if k.startswith("va_")]:
                del st.session_state[k]
            st.rerun()

    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:11px;color:#B7B7B7;margin-top:4px">'
        "💡 Instagram CDN-URLs en YouTube werken het betrouwbaarst. "
        "Instagram page-URLs kunnen geblokkeerd worden vanuit cloud servers."
        "</p>",
        unsafe_allow_html=True,
    )

    if run and url:
        _run_analysis(url)

    if "va_result" in st.session_state:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        _render_results(st.session_state["va_result"])


def _run_analysis(url: str):
    """Downloads, transcribes, and analyzes the video. Stores result in session_state."""
    audio_path = None
    try:
        with st.status("Video analyseren...", expanded=True) as status:
            st.write("⏬ Audio downloaden...")
            audio_path, err = download_audio(url)
            if err:
                status.update(label="❌ Download mislukt", state="error")
                st.error(err)
                return

            st.write("🎙️ Transcriberen met Whisper...")
            transcript, err = transcribe(audio_path)
            if err:
                status.update(label="❌ Transcriptie mislukt", state="error")
                st.error(err)
                return

            st.write("🧠 Analyseren met GPT-4o...")
            analysis, err = analyze(transcript)
            if err:
                st.warning(f"Transcript beschikbaar maar analyse mislukt: {err}")
                analysis = {}

            status.update(label="✅ Analyse compleet", state="complete")

        st.session_state["va_result"] = {
            "url": url,
            "transcript": transcript,
            "analysis": analysis,
        }
        st.rerun()
    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.unlink(audio_path)
            except Exception:
                pass


def _render_results(result: dict):
    """Renders the analysis result from session_state."""
    analysis = result.get("analysis", {})
    transcript = result.get("transcript", "")
    url = result.get("url", "")

    # Content type badge
    ct = analysis.get("content_type", "")
    if ct == "value":
        badge_color, badge_text = "#00C27A", "VALUE CONTENT"
    elif ct == "top_funnel":
        badge_color, badge_text = "#E9003A", "TOP FUNNEL"
    else:
        badge_color, badge_text = "#B7B7B7", "ANALYSED"

    header_cols = st.columns([1, 6])
    with header_cols[0]:
        st.markdown(
            f'<span style="display:inline-block;background:{badge_color}18;color:{badge_color};'
            f'padding:3px 10px;border-radius:2px;font-size:11px;font-weight:700;'
            f'font-family:Roboto Mono,monospace;letter-spacing:1px;'
            f'border:1px solid {badge_color}40;margin-top:6px">{badge_text}</span>',
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        if analysis.get("hook_type"):
            st.markdown(
                f'<span style="font-family:Roboto Mono,monospace;font-size:11px;'
                f'color:#B7B7B7;background:#1E1E1E;padding:3px 10px;border-radius:2px;'
                f'margin-top:6px;display:inline-block;border:1px solid #2a2a2a">'
                f'hook type: {analysis["hook_type"]}</span>',
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    # Hook + kernboodschap naast elkaar
    col1, col2 = st.columns(2)
    with col1:
        if analysis.get("hook"):
            st.markdown("**🪝 Hook**")
            st.markdown(
                f'<div style="background:#1E1E1E;border-left:3px solid #E9003A;'
                f'padding:12px 14px;border-radius:2px;font-family:Inter,sans-serif;'
                f'font-size:14px;color:#F5F5F5;line-height:1.5">'
                f'{analysis["hook"]}</div>',
                unsafe_allow_html=True,
            )
    with col2:
        if analysis.get("kernboodschap"):
            st.markdown("**💡 Kernboodschap**")
            st.info(analysis["kernboodschap"])

    # Samenvatting
    if analysis.get("samenvatting"):
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown("**📋 Samenvatting**")
        st.markdown(
            f'<div style="background:#1E1E1E;border:1px solid #2a2a2a;'
            f'padding:14px 16px;border-radius:4px;font-family:Inter,sans-serif;'
            f'font-size:13px;color:#B7B7B7;line-height:1.6">'
            f'{analysis["samenvatting"]}</div>',
            unsafe_allow_html=True,
        )

    # Nak dit
    if analysis.get("nak_dit"):
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.success(f"🚀 **Nak dit:** {analysis['nak_dit']}")

    # URL + transcript (collapsed)
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    detail_col1, detail_col2 = st.columns(2)
    with detail_col1:
        if url:
            st.link_button("🔗 Bekijk originele video", url)
    with detail_col2:
        pass

    with st.expander("📝 Volledig transcript"):
        st.text(transcript or "Geen transcript beschikbaar (stille of muziek-only video).")

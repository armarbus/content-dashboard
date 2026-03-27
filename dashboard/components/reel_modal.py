# dashboard/components/reel_modal.py
"""
Shared modal component for reel detail view + Nak dit script generator.
Imported by all tab modules.
"""
import os
import streamlit as st
from openai import OpenAI

NAKIT_SYSTEM_PROMPT = """Je bent een content strateeg voor Ayman, een hybrid performance coach.
Zijn doelgroep: mannen 16-35. Merk: hybrid training, discipline, masculinity, lifestyle.
Schrijf een volledig Reel-script op basis van een viral reel van een concurrent.
Output exact dit formaat (geen extra tekst):
**Hook:** [opening line — eerste 3 seconden]
**Punt 1:** [eerste punt of actie — 5-10 seconden]
**Punt 2:** [tweede punt of actie — 5-10 seconden]
**Punt 3:** [derde punt of actie — 5-10 seconden]
**CTA:** [call to action — laatste 3 seconden]
Schrijf in het Nederlands. Wees direct, energiek, masculine."""


def generate_nakit_script(reel: dict) -> str:
    """Calls OpenAI to generate a Nak dit script for the given reel."""
    api_key = st.secrets.get("OPENAI_API_KEY") if hasattr(st, "secrets") else None
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    transcript_section = ""
    if reel.get("transcript"):
        transcript_section = f"\nTranscriptie: {reel['transcript'][:500]}"

    user_prompt = (
        f"Viral reel van @{reel.get('competitor_handle', 'onbekend')}:\n"
        f"Hook: {reel.get('hook', '')}\n"
        f"Thema: {reel.get('theme', '')}\n"
        f"Hook type: {reel.get('hook_type', '')}\n"
        f"Waarom viral: {reel.get('ai_why', '')}\n"
        f"Views: {reel.get('views', 0):,}{transcript_section}\n\n"
        "Schrijf nu Ayman's versie van dit script."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": NAKIT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=400,
    )
    return response.choices[0].message.content


@st.dialog("Reel details", width="large")
def show_reel_modal(reel: dict):
    """Full-detail modal for a single reel, with Nak dit script generator."""
    col_left, col_right = st.columns([2, 3])

    with col_left:
        if reel.get("thumbnail_url"):
            st.image(reel["thumbnail_url"], use_container_width=True)
        if reel.get("video_url"):
            st.link_button("🔗 Bekijk op Instagram", reel["video_url"])

    with col_right:
        score = reel.get("viral_score", 0)
        badge = "🟢" if score >= 70 else "🟡" if score >= 50 else "🔴"

        st.markdown(f"**@{reel.get('competitor_handle', '—')}** · {str(reel.get('posted_at', ''))[:10]}")
        st.markdown(f"{badge} Viral Score: **{score}**")

        st.markdown(f"**Hook:** {reel.get('hook', '—')}")
        col_chips1, col_chips2 = st.columns(2)
        with col_chips1:
            st.caption(f"Type: `{reel.get('hook_type', '—')}`")
        with col_chips2:
            st.caption(f"Thema: `{reel.get('theme', '—')}`")

        cols = st.columns(3)
        cols[0].metric("Views", f"{reel.get('views', 0):,}")
        cols[1].metric("Likes", f"{reel.get('likes', 0):,}")
        cols[2].metric("Comments", f"{reel.get('comments', 0):,}")

        if reel.get("ai_why"):
            st.markdown(f"**Waarom viral:** {reel['ai_why']}")

        if reel.get("transcript"):
            with st.expander("📝 Transcriptie"):
                st.text(reel["transcript"])

        st.divider()

        cache_key = f"nakit_{reel['reel_id']}"
        if st.button("🚀 Nak dit", type="primary"):
            if cache_key not in st.session_state:
                with st.spinner("Script genereren..."):
                    try:
                        st.session_state[cache_key] = generate_nakit_script(reel)
                    except Exception as e:
                        st.error(f"Script genereren mislukt: {e}")

        if cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])

# dashboard/components/reel_modal.py
"""
Shared modal component for reel detail view + Nak dit script generator.
Imported by all tab modules.
"""
import os
import streamlit as st
from openai import OpenAI

NAKIT_SYSTEM_PROMPT = """Je bent een elite content strateeg voor Ayman (@aymanraoul), een hybrid performance coach.
Doelgroep: ambitieuze mannen 16-35. Merk: hybrid training, discipline, masculinity, esthetische lifestyle.
Ayman's stijl: rustig, zelfverzekerd, authentiek — geen schreeuwerig energy, maar quiet authority.
Storytelling vibe: cinematisch, contrast-gedreven (vroeger vs. nu), diepgang onder de oppervlakte.

Op basis van een viral reel van een concurrent schrijf jij Ayman's versie. Gebruik de hook/thema als inspiratie, maar maak het 100% Ayman's eigen verhaal.

Output EXACT dit formaat (geen extra tekst ervoor of erna):

[1-2 zinnen waarom dit concept viral gaat en wat de emotionele kern is]

**🎙️ Voice-over Script: [Pakkende Nederlandse Titel] ([totale duur] sec)**

**(0-[X] sec) [Stemming/Toon]:**
"[Voice-over tekst — kalm, beeldend, trekt meteen aan]"

**([X]-[Y] sec) [Stemming/Toon]:**
"[Voice-over tekst — eerlijk, direct, raakt de kijker]"

**([Y]-[Z] sec) [Stemming/Toon]:**
"[Voice-over tekst — krachtig, autoritair, de les]"

**([Z]-[eind] sec) [Stemming/Toon]:**
"[Voice-over tekst — inspirerend, afsluitend, zachte CTA]"

---

**🎬 B-roll Suggesties:**

**Intro:** [Cinematisch openingsshot — stel de sfeer in]
**Midden:** [Actie/contrast shots — ondersteun het verhaal]
**Contrast:** [Vroeger vs. nu shot — versterkt de transformatie]
**Outro:** [Krachtig afsluitend beeld — blijft hangen]

Schrijf in het Nederlands. Stijl: kalm, poëtisch maar masculien, nooit cliché. Max 45 seconden totaal."""


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
        model="gpt-4o",
        messages=[
            {"role": "system", "content": NAKIT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.75,
        max_tokens=900,
    )
    return response.choices[0].message.content


@st.dialog("Reel details", width="large")
def show_reel_modal(reel: dict):
    """Full-detail modal for a single reel, with Nak dit script generator."""
    col_left, col_right = st.columns([2, 3])

    with col_left:
        if reel.get("thumbnail_url"):
            st.image(reel["thumbnail_url"], width=300)
        if reel.get("video_url"):
            st.link_button("🔗 Bekijk op Instagram", reel["video_url"])

    with col_right:
        score = reel.get("viral_score", 0)
        if score >= 70:
            s_color, s_bg = "#00C27A", "rgba(0,194,122,0.10)"
        elif score >= 50:
            s_color, s_bg = "#E9003A", "rgba(233,0,58,0.10)"
        else:
            s_color, s_bg = "#B7B7B7", "rgba(183,183,183,0.08)"

        st.markdown(
            f'<p style="font-family:Inter,sans-serif;font-size:12px;color:#B7B7B7;margin:0 0 6px 0">'
            f'<span style="color:#F5F5F5;font-weight:700">@{reel.get("competitor_handle","—")}</span>'
            f' &nbsp;·&nbsp; {str(reel.get("posted_at",""))[:10]}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<span style="display:inline-block;background:{s_bg};color:{s_color};'
            f'padding:2px 10px;border-radius:2px;font-size:12px;font-weight:700;'
            f'font-family:Roboto Mono,monospace;letter-spacing:0.5px;'
            f'border:1px solid {s_color}40;margin-bottom:10px">SCORE {score}</span>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<p style="font-family:Inter,sans-serif;font-size:14px;font-weight:600;'
            f'color:#F5F5F5;line-height:1.5;margin:0 0 8px 0">'
            f'{reel.get("hook", "—")}</p>',
            unsafe_allow_html=True,
        )
        col_chips1, col_chips2 = st.columns(2)
        with col_chips1:
            st.markdown(
                f'<span style="font-family:Roboto Mono,monospace;font-size:11px;'
                f'color:#B7B7B7;background:#1E1E1E;padding:2px 8px;border-radius:2px">'
                f'{reel.get("hook_type","—")}</span>',
                unsafe_allow_html=True,
            )
        with col_chips2:
            st.markdown(
                f'<span style="font-family:Roboto Mono,monospace;font-size:11px;'
                f'color:#B7B7B7;background:#1E1E1E;padding:2px 8px;border-radius:2px">'
                f'{reel.get("theme","—")}</span>',
                unsafe_allow_html=True,
            )

        cols = st.columns(3)
        cols[0].metric("VIEWS", f"{reel.get('views', 0):,}")
        cols[1].metric("LIKES", f"{reel.get('likes', 0):,}")
        cols[2].metric("COMMENTS", f"{reel.get('comments', 0):,}")

        if reel.get("ai_why"):
            st.markdown(
                f'<p style="font-family:Inter,sans-serif;font-size:13px;color:#B7B7B7;'
                f'border-left:2px solid #E9003A;padding-left:10px;margin:8px 0">'
                f'{reel["ai_why"]}</p>',
                unsafe_allow_html=True,
            )

        if reel.get("transcript"):
            with st.expander("📝 Transcriptie"):
                st.text(reel["transcript"])

        st.divider()

        cache_key = f"nakit_{reel['reel_id']}"
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            if st.button("🚀 NAK DIT", type="primary", use_container_width=True):
                with st.spinner("Script genereren..."):
                    try:
                        st.session_state[cache_key] = generate_nakit_script(reel)
                    except Exception as e:
                        st.error(f"Script genereren mislukt: {e}")
        with col_btn2:
            if cache_key in st.session_state:
                if st.button("↺ OPNIEUW", use_container_width=True):
                    del st.session_state[cache_key]
                    st.rerun()

        if cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])

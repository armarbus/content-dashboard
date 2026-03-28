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
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            if st.button("🚀 Nak dit", type="primary", use_container_width=True):
                with st.spinner("Script genereren..."):
                    try:
                        st.session_state[cache_key] = generate_nakit_script(reel)
                    except Exception as e:
                        st.error(f"Script genereren mislukt: {e}")
        with col_btn2:
            if cache_key in st.session_state:
                if st.button("🔄 Opnieuw", use_container_width=True):
                    del st.session_state[cache_key]
                    st.rerun()

        if cache_key in st.session_state:
            st.markdown(st.session_state[cache_key])

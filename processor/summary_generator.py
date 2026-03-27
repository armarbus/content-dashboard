# processor/summary_generator.py
"""
Generates a weekly summary using OpenAI based on the top reels of the week.
"""
import os
import json
import re
from openai import OpenAI


SUMMARY_SYSTEM_PROMPT = """Je bent een content strateeg voor Ayman, een hybrid performance coach.
Zijn doelgroep: mannen 16-35. Merk: hybrid training, discipline, masculinity, lifestyle.
Analyseer de top Instagram Reels van deze week van zijn concurrenten en geef een wekelijkse samenvatting
als JSON met exact deze keys: trending_themes, best_hook_types, top3_to_copy, weekly_advice.
Schrijf in het Nederlands. Wees direct en praktisch — Ayman post 3 Shorts per dag."""

FALLBACK_SUMMARY = {
    "trending_themes": "Geen data beschikbaar voor deze week.",
    "best_hook_types": "",
    "top3_to_copy": "",
    "weekly_advice": "",
}


def generate_weekly_summary(top_reels: list, week_start_date: str) -> dict:
    """
    Takes a list of top reels and generates a weekly summary dict.
    Returns a dict ready for upsert into the summaries table.
    """
    if not top_reels:
        return {"week_start_date": week_start_date, **FALLBACK_SUMMARY}

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    reels_text = "\n".join([
        f"- Hook: '{r.get('hook', '')}' | Type: {r.get('hook_type', '')} | "
        f"Thema: {r.get('theme', '')} | Score: {r.get('viral_score', 0)} | "
        f"Account: @{r.get('competitor_handle', '')} | Waarom: {r.get('ai_why', '')}"
        for r in top_reels[:15]
    ])

    user_prompt = f"""Week van {week_start_date}. Top Reels van concurrenten:

{reels_text}

Geef een JSON samenvatting met:
- trending_themes: 2-3 zinnen over welke thema's domineren
- best_hook_types: welke hook-types het best werkten en waarom
- top3_to_copy: top 3 concrete video-ideeën voor Ayman om na te maken (met hook-suggestie)
- weekly_advice: 1 aanbeveling voor Aymanʼs content strategie deze week"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        raw = response.choices[0].message.content
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(cleaned)
        # Coerce all fields to strings in case OpenAI returns list/dict
        for key in ("trending_themes", "best_hook_types", "top3_to_copy", "weekly_advice"):
            if key in data and not isinstance(data[key], str):
                data[key] = json.dumps(data[key], ensure_ascii=False)
        return {"week_start_date": week_start_date, **data}
    except Exception as e:
        print(f"  ⚠️  Summary generation error: {e}")
        return {"week_start_date": week_start_date, **FALLBACK_SUMMARY}

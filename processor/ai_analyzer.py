# processor/ai_analyzer.py
"""
Sends each reel's metadata to OpenAI GPT-4o-mini for hook/theme/AI analysis.
"""
import os
import json
import re
from typing import Optional
from openai import OpenAI


SYSTEM_PROMPT = """Je bent een content analist voor Ayman, een hybrid performance coach.
Zijn merk: kracht + hardlopen, discipline, stoïcijnse mindset, masculine lifestyle.
Doelgroep: mannen 16-35 die sterker, droger en mentaal scherper willen worden.
Merkboodschap: "Bouw een hybride lichaam. Bouw discipline. Bouw jezelf."
Zijn eigen hook-stijl: identiteit ("mannen die trainen winnen"), tegenstelling
("stop met alleen bulken"), discipline ("je hoeft je niet goed te voelen om te winnen"),
lifestyle ("sober living, early mornings, consistent training").

Analyseer de aangeleverde Instagram Reel en geef ALLEEN een JSON object terug (geen markdown):
{
  "hook": "eerste 6-8 woorden van de tekst, of korte beschrijving als er geen tekst is",
  "hook_type": "een van: identiteit | tegenstelling | discipline | transformatie | lifestyle | anders",
  "theme": "een van: hybrid | kracht | voeding | mindset | lifestyle | anders",
  "ai_why": "1-2 zinnen waarom deze video viral gaat in de hybrid/fitness niche",
  "ai_your_version": "concrete hook of idee hoe Ayman dit kan nabouwen voor zijn merk"
}"""

FALLBACK = {
    "hook": "Geen tekst beschikbaar",
    "hook_type": "anders",
    "theme": "anders",
    "ai_why": "",
    "ai_your_version": "",
}


def extract_hook_text(caption: Optional[str]) -> str:
    """
    Extracts the first meaningful 6-8 words from a caption.
    Returns empty string if caption starts with hashtag/emoji or is empty.
    """
    if not caption:
        return ""
    stripped = caption.strip()
    if not stripped or stripped[0] in ("#", "@") or not stripped[0].isalpha():
        return ""
    words = stripped.split()[:8]
    return " ".join(words)


def build_prompt_content(caption: str, handle: str) -> str:
    hook_hint = extract_hook_text(caption)
    return f"""Account: @{handle}
Caption: {caption or "(geen caption beschikbaar)"}
Mogelijke hook (eerste woorden): {hook_hint or "(niet extraheerbaar, genereer zelf)"}

Geef je JSON analyse:"""


def parse_ai_response(raw: str) -> dict:
    """Parses OpenAI response string into dict. Returns fallback on any error."""
    try:
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        data = json.loads(cleaned)
        for key in ("hook", "hook_type", "theme", "ai_why", "ai_your_version"):
            if key not in data:
                data[key] = FALLBACK[key]
        return data
    except Exception:
        return FALLBACK.copy()


def analyze_reel(caption: str, handle: str) -> dict:
    """
    Calls OpenAI with reel metadata and returns parsed analysis dict.
    Falls back gracefully on API errors.
    """
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt_content(caption, handle)},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        raw = response.choices[0].message.content
        return parse_ai_response(raw)
    except Exception as e:
        print(f"  ⚠️  OpenAI error for @{handle}: {e}")
        return FALLBACK.copy()

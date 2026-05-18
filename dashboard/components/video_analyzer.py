# dashboard/components/video_analyzer.py
"""
Ad-hoc video analyser: download audio → Whisper transcript → GPT-4o analysis.
Supports Instagram CDN URLs, Instagram page URLs, and YouTube Shorts/videos.
"""
import os
import json
import re
import tempfile
import requests
from openai import OpenAI


def _get_client() -> OpenAI:
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        api_key = None
    return OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY", ""))


def _download_direct(url: str, tmp_path: str) -> bool:
    """Direct HTTP download — works for Apify/CDN video URLs."""
    try:
        resp = requests.get(url, timeout=60, stream=True,
                            headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        ct = resp.headers.get("Content-Type", "")
        if not (ct.startswith("video/") or ct.startswith("audio/")):
            return False
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        return os.path.getsize(tmp_path) > 2000
    except Exception:
        return False


def _download_ytdlp(url: str, tmp_path: str) -> bool:
    """yt-dlp download — handles Instagram page URLs and YouTube."""
    try:
        import yt_dlp
        base = tmp_path.removesuffix(".mp4")
        ydl_opts = {
            "outtmpl": base + ".%(ext)s",
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for ext in ("mp4", "m4a", "webm", "mp3", "ogg", "opus"):
            candidate = f"{base}.{ext}"
            if os.path.exists(candidate) and os.path.getsize(candidate) > 2000:
                if candidate != tmp_path:
                    os.rename(candidate, tmp_path)
                return True
        return False
    except Exception as e:
        print(f"yt-dlp error: {e}")
        return False


def download_audio(url: str) -> tuple[str | None, str]:
    """
    Downloads audio/video from URL to a temp file.
    Returns (tmp_path, error_msg). Caller must delete the file.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp_path = tmp.name
    tmp.close()

    if _download_direct(url, tmp_path):
        return tmp_path, ""

    if _download_ytdlp(url, tmp_path):
        return tmp_path, ""

    try:
        os.unlink(tmp_path)
    except Exception:
        pass
    return None, (
        "Video kon niet worden gedownload. Instagram blokkeert soms downloads vanuit "
        "cloud servers. Probeer een directe CDN-URL of een YouTube Short URL."
    )


def transcribe(audio_path: str) -> tuple[str, str]:
    """Whisper transcription. Returns (transcript, error_msg)."""
    size_mb = os.path.getsize(audio_path) / 1_000_000
    if size_mb > 24:
        return "", f"Bestand te groot ({size_mb:.1f} MB). Maximum is 24 MB."
    try:
        client = _get_client()
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(model="whisper-1", file=f)
        return result.text, ""
    except Exception as e:
        return "", f"Transcriptie mislukt: {e}"


_ANALYSIS_SYSTEM = """Je bent een content strateeg voor hybrid performance creators.
Analyseer het transcript van een Instagram Reel of YouTube Short.
Geef ALLEEN een JSON object terug (geen markdown, geen uitleg):
{
  "hook": "De hook — eerste zin of actie die direct de aandacht trekt",
  "kernboodschap": "De centrale les of boodschap in 1-2 zinnen",
  "samenvatting": "Samenvatting van de video in 3-5 zinnen",
  "content_type": "value" of "top_funnel",
  "hook_type": "identiteit | tegenstelling | discipline | transformatie | lifestyle | anders",
  "nak_dit": "Concreet idee hoe jij dit concept kunt nabootsen voor je eigen merk (1-2 zinnen)"
}"""


def analyze(transcript: str) -> tuple[dict, str]:
    """GPT-4o analysis of transcript. Returns (analysis_dict, error_msg)."""
    if not transcript or len(transcript.strip()) < 15:
        return {}, "Transcript te kort — mogelijk stille of muziek-only video."
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": _ANALYSIS_SYSTEM},
                {"role": "user", "content": f"Transcript:\n{transcript[:3000]}"},
            ],
            temperature=0.3,
            max_tokens=500,
        )
        raw = response.choices[0].message.content
        cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
        return json.loads(cleaned), ""
    except Exception as e:
        return {}, f"Analyse mislukt: {e}"

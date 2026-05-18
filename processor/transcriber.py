# processor/transcriber.py
"""
Transcribes all reels using OpenAI Whisper.
Primary: direct CDN download (videoUrl from Apify).
Fallback: yt-dlp for Instagram page URLs when CDN is unavailable.
"""
import os
import tempfile
import requests
from openai import OpenAI

TOP_N_TRANSCRIBE = 9999  # kept for backward compat with main.py import; effectively unlimited


def _download_direct(url: str, tmp_path: str) -> bool:
    """Download video from a direct CDN URL. Returns True on success."""
    try:
        head = requests.head(url, timeout=10, allow_redirects=True)
        if not head.headers.get("Content-Type", "").startswith("video/"):
            return False
        resp = requests.get(url, timeout=60, stream=True)
        resp.raise_for_status()
        with open(tmp_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception:
        return False


def _download_ytdlp(url: str, tmp_path: str) -> bool:
    """Download video via yt-dlp (handles Instagram page URLs). Returns True on success."""
    try:
        import yt_dlp
        base = tmp_path.removesuffix(".mp4")
        ydl_opts = {
            "outtmpl": base + ".%(ext)s",
            "format": "mp4/best[ext=mp4]/best",
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for ext in ("mp4", "webm", "mkv", "mov"):
            candidate = f"{base}.{ext}"
            if os.path.exists(candidate):
                if candidate != tmp_path:
                    os.rename(candidate, tmp_path)
                return True
        return False
    except Exception as e:
        print(f"    yt-dlp failed: {e}")
        return False


def transcribe_top_reels(scored_reels: list[dict], top_n: int = TOP_N_TRANSCRIBE) -> dict[str, str]:
    """
    Transcribes up to top_n reels sorted by viral_score (default = all).
    Tries direct CDN download first, falls back to yt-dlp for page URLs.
    Returns dict mapping reel_id -> transcript text.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("  ⚠️  OPENAI_API_KEY not set — skipping transcription")
        return {}

    client = OpenAI(api_key=api_key)
    candidates = sorted(scored_reels, key=lambda r: r.get("viral_score", 0), reverse=True)[:top_n]
    transcripts: dict[str, str] = {}

    for reel in candidates:
        reel_id = reel.get("reel_id", "")
        video_url = reel.get("video_url", "")
        if not reel_id or not video_url:
            continue

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name

            downloaded = _download_direct(video_url, tmp_path)
            if not downloaded:
                print(f"  ↩  Direct download failed for {reel_id}, trying yt-dlp...")
                downloaded = _download_ytdlp(video_url, tmp_path)

            if not downloaded or not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                print(f"  ⚠️  Could not download {reel_id} — skipping")
                continue

            with open(tmp_path, "rb") as fp:
                result = client.audio.transcriptions.create(model="whisper-1", file=fp)
            transcripts[reel_id] = result.text
            print(f"  ✅ Transcribed {reel_id}: {result.text[:60]}...")

        except Exception as e:
            print(f"  ⚠️  Transcription failed for {reel_id}: {e}")

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return transcripts

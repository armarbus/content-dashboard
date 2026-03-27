# processor/transcriber.py
"""
Transcribes top-N reels by viral_score using OpenAI Whisper.
Non-fatal: exceptions per reel are logged and skipped.
"""
import os
import tempfile
import requests
from openai import OpenAI

TOP_N_TRANSCRIBE = 20  # single source of truth, imported by main.py


def transcribe_top_reels(scored_reels: list[dict], top_n: int = TOP_N_TRANSCRIBE) -> dict[str, str]:
    """
    Downloads and transcribes the top_n reels by viral_score.
    Returns dict mapping reel_id -> transcript text.
    Only processes reels with a direct video URL (Content-Type: video/*).
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("  ⚠️  OPENAI_API_KEY not set — skipping transcription")
        return {}
    client = OpenAI(api_key=api_key)
    sorted_reels = sorted(scored_reels, key=lambda r: r.get("viral_score", 0), reverse=True)
    candidates = sorted_reels[:top_n]

    transcripts: dict[str, str] = {}

    for reel in candidates:
        reel_id = reel.get("reel_id", "")
        if not reel_id:
            continue

        video_url = reel.get("video_url")
        if not video_url:
            continue

        # Skip obvious Instagram page URLs (not direct video files)
        if "instagram.com/reel/" in video_url and ".mp4" not in video_url:
            continue

        tmp_path = None
        try:
            # Verify Content-Type before downloading
            head = requests.head(video_url, timeout=10, allow_redirects=True)
            content_type = head.headers.get("Content-Type", "")
            if not content_type.startswith("video/"):
                print(f"  ⚠️  Skipping {reel_id}: Content-Type={content_type!r}")
                continue

            # Download to temp file
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)

            # Transcribe
            with open(tmp_path, "rb") as fp:
                result = client.audio.transcriptions.create(model="whisper-1", file=fp)
            transcripts[reel_id] = result.text
            print(f"  ✅ Transcribed {reel_id}: {result.text[:60]}...")

        except Exception as e:
            print(f"  ⚠️  Transcription failed for {reel_id}: {e}")
            continue

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    return transcripts

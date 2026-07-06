"""
Transcript Client - fetches real YouTube transcript text via TranscriptAPI.com
(a hosted, reliable service - avoids the cloud-IP blocking that broke both
youtube-transcript-api and yt-dlp when run directly from this AWS instance).
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

TRANSCRIPT_API_KEY = os.getenv("TRANSCRIPT_API_KEY")

TRANSCRIPT_API_KEY = os.getenv("TRANSCRIPT_API_KEY")
TRANSCRIPT_API_BASE = "https://transcriptapi.com/api/v2/youtube/transcript"


def fetch_full_transcript(video_url: str) -> list:
    """
    Fetches the full transcript with timestamps for a YouTube video.
    Returns a list of {"start": seconds, "text": "..."} entries, or an
    empty list if unavailable (e.g. captions disabled for this video).
    """
    headers = {"Authorization": f"Bearer {TRANSCRIPT_API_KEY}"}
    params = {"video_url": video_url, "format": "json", "include_timestamp": "true"}

    try:
        response = requests.get(TRANSCRIPT_API_BASE, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            print(f"[transcript_client] Request failed: {response.status_code} - {response.text[:200]}")
            return []

        data = response.json()
        return data.get("segments", data.get("transcript", []))
    except Exception as e:
        print(f"[transcript_client] Error fetching transcript: {e}")
        return []


def extract_segment_text(transcript: list, start_seconds: int, end_seconds: int) -> str:
    """
    Extracts only the transcript text spoken between start_seconds and
    end_seconds - today's actual assigned video segment - so quiz/interview
    generation can be grounded in exactly what was said in that timeframe.
    """
    if not transcript:
        return ""

    relevant_lines = []
    for entry in transcript:
        entry_time = entry.get("start", 0)
        if isinstance(entry_time, str):
            continue
        if start_seconds <= entry_time <= end_seconds:
            relevant_lines.append(entry.get("text", ""))

    return " ".join(relevant_lines)

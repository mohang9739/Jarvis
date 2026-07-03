import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from supabase import create_client
from ai_client import ask_ai_json

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_current_week_topic():
    """
    Determines this week's topic from the 21-week roadmap.
    For now, uses a simple week-number calculation from a fixed start date -
    this should be refined once the actual roadmap start date is confirmed.
    """
    ROADMAP = {
        1: "Linux command line basics file system permissions",
        2: "Bash scripting fundamentals",
        3: "Networking fundamentals TCP IP DNS",
        4: "Git version control fundamentals",
        5: "Python Basics",
        6: "DevOps for Python",
        7: "Python for API",
        8: "AWS fundamentals",
        9: "Docker Basics",
        10: "Advanced Docker",
        11: "Jenkins",
        12: "GitHub Actions",
        13: "Terraform Basic to Advanced",
        14: "Kubernetes Basics",
        15: "Advanced Kubernetes",
        16: "GitOps ArgoCD Helm",
        17: "Observability Prometheus Grafana",
        18: "DevSecOps",
        19: "AI for DevOps",
        20: "System Design and IDP Backstage concepts",
        21: "Resume ATS and Interview Practice",
    }
    # Placeholder: week 1. Replace with real week-tracking logic once confirmed.
    week_number = 1
    topic = ROADMAP.get(week_number, "DevOps fundamentals")
    return week_number, topic


def search_youtube_candidates(topic: str, max_results: int = 10) -> list:
    """Open search on YouTube for the topic - no fixed trusted-channel bias."""
    request = youtube.search().list(
        part="snippet",
        q=f"{topic} tutorial DevOps",
        type="video",
        maxResults=max_results,
        order="relevance",
        relevanceLanguage="en",
        videoDuration="medium"
    )
    response = request.execute()

    candidates = []
    for item in response.get("items", []):
        candidates.append({
            "video_id": item["id"]["videoId"],
            "title": item["snippet"]["title"],
            "channel_id": item["snippet"]["channelId"],
            "channel_name": item["snippet"]["channelTitle"],
            "description": item["snippet"]["description"],
            "published_at": item["snippet"]["publishedAt"]
        })
    return candidates


def get_video_stats(video_ids: list) -> dict:
    """Fetches duration and stats for scoring - NOT used for popularity bias, only duration/recency."""
    request = youtube.videos().list(
        part="contentDetails,statistics",
        id=",".join(video_ids)
    )
    response = request.execute()
    stats = {}
    for item in response.get("items", []):
        stats[item["id"]] = {
            "duration": item["contentDetails"]["duration"],
        }
    return stats


def get_last_week_channel() -> str:
    """Checks weekly_plan for last week's selected channel, for continuity scoring."""
    result = supabase.table("weekly_plan").select("*").order("created_at", desc=True).limit(1).execute()
    if result.data:
        return result.data[0].get("channel_id")
    return None

def score_candidate(candidate: dict, topic: str, last_week_channel: str) -> dict:
    """
    Scores a single video candidate using AI reasoning - hands-on quality and
    engagement/narrative quality weighted highest, relevance floor, recency,
    duration. NO popularity metrics (views/likes) used at all.
    """
    prompt = f"""
Evaluate this YouTube video as a candidate for a DevOps/Platform Engineer interview-prep learning video.

Topic this week: {topic}
Video title: {candidate['title']}
Channel: {candidate['channel_name']}
Description: {candidate['description'][:300]}
Published: {candidate['published_at']}

Score on these criteria (each 1-10):
- relevance: does this genuinely cover the topic, not just loosely related
- hands_on: does the title/description suggest practical, hands-on demonstration vs pure theory
- engagement_quality: does this sound genuinely well-explained and engaging based on title/description,
  not clickbait
- recency: how recent is this, given DevOps tooling changes over time (recent = higher score)

Do NOT consider view counts, likes, or subscriber counts - none of that data is provided or relevant.

Also determine: does this look like a full match for the topic, a partial match (some gap), or no match
(reject this candidate)?

Return JSON:
{{
  "relevance": 7,
  "hands_on": 8,
  "engagement_quality": 7,
  "recency": 6,
  "match_type": "full",
  "reject": false,
  "reject_reason": null
}}
"""
    return ask_ai_json(prompt)


def pick_best_video(topic: str) -> dict:
    """Full pipeline: search, score, apply continuity bonus, pick winner."""
    candidates = search_youtube_candidates(topic)
    last_week_channel = get_last_week_channel()

    scored = []
    for candidate in candidates:
        score_result = score_candidate(candidate, topic, last_week_channel)

        if score_result.get("reject", False):
            continue

        # Hands-on and engagement weighted highest (per original design)
        total_score = (
            score_result.get("hands_on", 0) * 2 +
            score_result.get("engagement_quality", 0) * 2 +
            score_result.get("relevance", 0) * 1.5 +
            score_result.get("recency", 0) * 1
        )

        # Continuity bonus - not a hard rule, just a tie-breaker boost
        if last_week_channel and candidate["channel_id"] == last_week_channel:
            total_score += 3

        scored.append({**candidate, "score": total_score, "match_type": score_result.get("match_type")})

    if not scored:
        return None

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[0]


def run_video_select():
    """Entry point - picks this week's video and saves it to weekly_plan."""
    week_number, topic = get_current_week_topic()
    winner = pick_best_video(topic)

    if not winner:
        print(f"[video_select] No suitable video found for week {week_number}: {topic}")
        return None

    supabase.table("weekly_plan").insert({
        "week_number": week_number,
        "day_of_week": "Monday",
        "topic": topic,
        "video_url": f"https://youtube.com/watch?v={winner['video_id']}",
        "channel_id": winner["channel_id"],
        "channel_name": winner["channel_name"],
        "status": "selected"
    }).execute()

    print(f"[video_select] Selected: {winner['title']} ({winner['channel_name']}) - score: {winner['score']}")
    return winner

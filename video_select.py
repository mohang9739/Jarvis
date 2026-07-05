import os
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from ai_client import ask_ai, ask_ai_json
from db_client import supabase

youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_current_week_topic():
    """
    Determines the current week's topic from the 21-week roadmap.
    Uses REAL data with a genuine readiness gate: only advances to the next
    week if last week's quiz was passed AND last week's interview questions
    were genuinely cleared (average score >= 7/10). If either gate fails,
    repeats the SAME week's topic - reinforcing weak material instead of
    advancing to new content on a shaky foundation.

    Uses AI-based topic matching for the quiz gate, since scores.topic and
    the roadmap's topic text are independently worded (e.g. "Linux file
    permissions (chmod)" vs "Linux command line basics file system
    permissions" - same real subject, different exact text) - exact string
    matching would incorrectly show quiz_passed=False even for a real pass.
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

    existing = supabase.table("weekly_plan").select("week_number, topic").order("week_number", desc=True).limit(1).execute()

    if not existing.data:
        return 1, ROADMAP.get(1)

    last_week_number = existing.data[0]["week_number"]
    last_week_topic = existing.data[0]["topic"]

    # GATE 1: check if last week's quiz was genuinely passed, using AI to match
    # topic strings that refer to the same real subject but are worded differently
    quiz_passed = False
    recent_scores = supabase.table("scores").select("*").order("created_at", desc=True).limit(5).execute()
    for score_row in recent_scores.data:
        topic_match_prompt = (
            "Does this quiz topic genuinely refer to the same real subject as this roadmap topic? "
            'Quiz topic: "' + score_row.get("topic", "") + '" '
            'Roadmap topic: "' + last_week_topic + '" '
            "Reply with only YES or NO."
        )
        match_result = ask_ai(topic_match_prompt)
        if "YES" in match_result.upper():
            quiz_passed = score_row.get("passed", False)
            break

    # GATE 2: check if last week's interview questions were genuinely cleared (average score >= 7/10)
    interview_result = supabase.table("interview_sessions").select("score").eq("topic", last_week_topic).execute()
    interview_scores = [row["score"] for row in interview_result.data if row.get("score") is not None]
    interview_cleared = (sum(interview_scores) / len(interview_scores) >= 7) if interview_scores else False

    if quiz_passed and interview_cleared:
        week_number = min(last_week_number + 1, 21)
    else:
        week_number = last_week_number
        print(f"[video_select] Week {last_week_number} ({last_week_topic}) not yet cleared - quiz_passed={quiz_passed}, interview_cleared={interview_cleared}. Repeating this week.")

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


def get_video_durations(video_ids: list) -> dict:
    """
    Fetches each video's duration in seconds - used only for sensible
    watch-plan reasoning (splitting long videos), NEVER for popularity bias.
    """
    import re
    request = youtube.videos().list(
        part="contentDetails",
        id=",".join(video_ids)
    )
    response = request.execute()

    durations = {}
    for item in response.get("items", []):
        iso_duration = item["contentDetails"]["duration"]
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        durations[item["id"]] = hours * 3600 + minutes * 60 + seconds
    return durations


def get_last_week_channel() -> str:
    """Checks weekly_plan for last week's selected channel, for continuity scoring."""
    result = supabase.table("weekly_plan").select("*").order("created_at", desc=True).limit(1).execute()
    if result.data:
        return result.data[0].get("channel_id")
    return None


def score_candidate(candidate: dict, topic: str, last_week_channel: str) -> dict:
    """
    Scores a single video candidate using AI reasoning - hands-on quality and
    engagement/narrative quality weighted highest, relevance floor, recency.
    NO popularity metrics (views/likes) used at all.
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


def extract_timestamp_range(description: str, topic: str, duration_seconds: int = None) -> dict:
    """
    Checks if the video description contains chapter timestamps, and if so,
    identifies which range covers the topic. If no timestamps exist, reasons
    about the video's total duration to suggest a sensible watch plan.
    """
    duration_note = f"Video duration: approximately {duration_seconds // 60} minutes." if duration_seconds else "Video duration unknown."

    prompt = f"""
This is a YouTube video description. Check if it contains chapter timestamps (like "0:00 Intro", "2:15 Topic Name").

Topic to find: {topic}
Description: {description[:1000]}
{duration_note}

If timestamps exist AND one clearly covers this topic, return that exact range.

If NO usable timestamps exist, reason about the video's duration instead:
- If it's a reasonably short video (under ~35 minutes), suggest watching it fully in one sitting today.
- If it's genuinely long (35+ minutes) with no chapters to guide a shorter segment, suggest a sensible
  split across 2-3 days instead of forcing the whole thing into one sitting - note this in "split_suggestion".

Return JSON:
{{
  "has_timestamps": false,
  "start_time": "0:00:00",
  "end_time": null,
  "split_suggestion": null
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

        total_score = (
            score_result.get("hands_on", 0) * 2 +
            score_result.get("engagement_quality", 0) * 2 +
            score_result.get("relevance", 0) * 1.5 +
            score_result.get("recency", 0) * 1
        )

        if last_week_channel and candidate["channel_id"] == last_week_channel:
            total_score += 3

        scored.append({**candidate, "score": total_score, "match_type": score_result.get("match_type")})

    if not scored:
        return None

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[0]


def run_video_select():
    """Entry point - picks this week's video, determines timing, saves to weekly_plan."""
    week_number, topic = get_current_week_topic()
    winner = pick_best_video(topic)

    if not winner:
        print(f"[video_select] No suitable video found for week {week_number}: {topic}")
        return None

    durations = get_video_durations([winner["video_id"]])
    duration_seconds = durations.get(winner["video_id"])

    timing = extract_timestamp_range(winner.get("description", ""), topic, duration_seconds)

    supabase.table("weekly_plan").insert({
        "week_number": week_number,
        "day_of_week": "Monday",
        "topic": topic,
        "video_url": f"https://youtube.com/watch?v={winner['video_id']}",
        "video_start_time": timing.get("start_time", "0:00:00"),
        "video_end_time": timing.get("end_time"),
        "channel_id": winner["channel_id"],
        "channel_name": winner["channel_name"],
        "status": "selected"
    }).execute()

    split_note = f" | {timing.get('split_suggestion')}" if timing.get("split_suggestion") else ""
    print(f"[video_select] Selected: {winner['title']} ({winner['channel_name']}) - score: {winner['score']}, timing: {timing.get('start_time')}-{timing.get('end_time')}{split_note}")
    return winner
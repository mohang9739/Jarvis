import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from googleapiclient.discovery import build
from ai_client import ask_ai, ask_ai_json
from db_client import supabase
from transcript_client import fetch_full_transcript, extract_segment_text
from fixed_video_map import get_week_config

youtube = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))


def get_current_week_topic():
    """
    Determines the current week's topic from the 20-week roadmap.
    Uses REAL data with a genuine readiness gate: only advances to the
    next week if last week's quiz was passed AND last week's interview
    questions were genuinely cleared (average score >= 7/10).
    """
    ROADMAP = {
        1: "Linux Basics - commands, file system navigation, permissions, and processes",
        2: "Linux Service Management - systemd, journalctl, process supervision",
        3: "Bash scripting fundamentals",
        4: "Networking fundamentals - TCP/IP, DNS resolution, OSI layers",
        5: "Git version control fundamentals",
        6: "Python Basics",
        7: "DevOps for Python - automation scripting, testing, and packaging",
        8: "AI Tools for DevOps - Copilot, Cursor, CLI agents to accelerate infra-as-code and scripting work",
        9: "Python for API - FastAPI, REST endpoint design",
        10: "AWS fundamentals - IAM, EC2, Auto Scaling Groups, Route53, and event-driven systems via SQS",
        11: "AWS Networking - VPC, subnets, security groups, NAT gateways, routing",
        12: "Terraform Basic to Advanced",
        13: "Docker - basics through advanced multi-stage builds and image optimization",
        14: "Kubernetes - basics through advanced (pods, deployments, services, ingress, autoscaling)",
        15: "GitOps ArgoCD Helm",
        16: "CI/CD - Jenkins fundamentals and GitHub Actions (Actions-first emphasis per current industry trend)",
        17: "Observability - Prometheus Grafana",
        18: "DevSecOps",
        19: "System Design and IDP Backstage concepts",
        20: "Resume ATS and Interview Practice",
    }

    existing = supabase.table("weekly_plan").select("week_number, topic").order("week_number", desc=True).limit(1).execute()

    if not existing.data:
        return 1, ROADMAP.get(1)

    last_week_number = existing.data[0]["week_number"]
    last_week_topic = existing.data[0]["topic"]

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

    interview_result = supabase.table("interview_sessions").select("score").eq("topic", last_week_topic).execute()
    interview_scores = [row["score"] for row in interview_result.data if row.get("score") is not None]
    interview_cleared = (sum(interview_scores) / len(interview_scores) >= 7) if interview_scores else False

    if quiz_passed and interview_cleared:
        week_number = min(last_week_number + 1, 20)
    else:
        week_number = last_week_number
        print(f"[video_select] Week {last_week_number} ({last_week_topic}) not yet cleared - quiz_passed={quiz_passed}, interview_cleared={interview_cleared}. Repeating this week.")

    topic = ROADMAP.get(week_number, "DevOps fundamentals")
    return week_number, topic


def search_youtube_candidates(topic: str, max_results: int = 10) -> list:
    """Open search on YouTube for the topic, biased toward comprehensive content."""
    request = youtube.search().list(
        part="snippet",
        q=f"{topic} complete course full tutorial",
        type="video",
        maxResults=max_results,
        order="relevance",
        relevanceLanguage="en"
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
    """Fetches each video's duration in seconds."""
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


def score_candidate(candidate: dict, topic: str, last_week_channel: str, duration_seconds: int = None) -> dict:
    """Scores a video candidate. pbc_depth is highest-weighted."""
    duration_note = f"Video duration: {duration_seconds // 60} minutes." if duration_seconds else "Video duration: unknown."

    prompt = f"""
Evaluate this YouTube video as a candidate for a DevOps/Platform Engineer interview-prep learning video.

Topic this week: {topic}
Video title: {candidate['title']}
Channel: {candidate['channel_name']}
Description: {candidate['description'][:300]}
Published: {candidate['published_at']}
{duration_note}

IMPORTANT: Cross-check the title/description's claimed scope against the actual duration above.
A video claiming broad coverage in only a few minutes CANNOT genuinely deliver that depth.

Score on these criteria (each 1-10):
- relevance: does this genuinely cover the topic
- hands_on: practical demonstration vs pure theory
- engagement_quality: well-explained and engaging, not clickbait
- recency: how recent, given DevOps tooling changes
- pbc_depth: deep enough for real PE/DevOps interview questions at product-based companies?

Return JSON:
{{
  "relevance": 7,
  "hands_on": 8,
  "engagement_quality": 7,
  "recency": 6,
  "pbc_depth": 6,
  "match_type": "full",
  "reject": false,
  "reject_reason": null
}}
"""
    return ask_ai_json(prompt)


def extract_timestamp_range(description: str, topic: str, duration_seconds: int = None) -> dict:
    """Checks for chapter timestamps in the video description."""
    duration_note = f"Video duration: approximately {duration_seconds // 60} minutes." if duration_seconds else "Video duration unknown."

    prompt = f"""
This is a YouTube video description. Check if it contains chapter timestamps.

Topic to find: {topic}
Description: {description[:1000]}
{duration_note}

If timestamps exist AND one clearly covers this topic, return that exact range, has_timestamps=true.
If NO usable timestamps exist, suggest a split across multiple days in "split_suggestion".

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
    """Full search pipeline: search, fetch durations, score, pick winner."""
    candidates = search_youtube_candidates(topic)
    last_week_channel = get_last_week_channel()

    if not candidates:
        return None

    video_ids = [c["video_id"] for c in candidates]
    durations = get_video_durations(video_ids)

    scored = []
    for candidate in candidates:
        duration_seconds = durations.get(candidate["video_id"])
        score_result = score_candidate(candidate, topic, last_week_channel, duration_seconds)

        if score_result.get("reject", False):
            continue

        total_score = (
            score_result.get("pbc_depth", 0) * 2.5 +
            score_result.get("hands_on", 0) * 2 +
            score_result.get("engagement_quality", 0) * 1.5 +
            score_result.get("relevance", 0) * 1.5 +
            score_result.get("recency", 0) * 1
        )

        if last_week_channel and candidate["channel_id"] == last_week_channel:
            total_score += 3

        scored.append({
            **candidate,
            "score": total_score,
            "match_type": score_result.get("match_type"),
            "pbc_depth": score_result.get("pbc_depth"),
            "duration_seconds": duration_seconds
        })

    if not scored:
        return None

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[0]


def _timestamp_to_seconds(timestamp_str: str) -> int:
    """Converts an 'H:MM:SS' string back into total seconds."""
    parts = timestamp_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + int(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    return 0


def format_seconds_to_timestamp(total_seconds: int) -> str:
    """Converts seconds into HH:MM:SS format."""
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours}:{minutes:02d}:{seconds:02d}"


def calculate_per_day_segments(duration_seconds: int, num_days: int) -> list:
    """Divides a long video's total duration evenly across the number of days."""
    if not duration_seconds or num_days <= 1:
        return [("0:00:00", None)] * max(num_days, 1)

    seconds_per_day = duration_seconds // num_days
    segments = []
    for i in range(num_days):
        start_seconds = i * seconds_per_day
        end_seconds = duration_seconds if i == num_days - 1 else (i + 1) * seconds_per_day
        segments.append((format_seconds_to_timestamp(start_seconds), format_seconds_to_timestamp(end_seconds)))
    return segments


def _save_fixed_week(week_number: int, topic: str, config: dict, all_days: list):
    """
    Saves weekly_plan rows using the pre-verified fixed video map.
    Handles both single-video (split by timestamp) and episode-list formats.
    Fetches real transcript once per video for transcript-grounded quiz/interview generation.
    """
    if config["type"] == "single":
        duration_seconds = config.get("duration_seconds", 3600)
        per_day_segments = calculate_per_day_segments(duration_seconds, len(all_days))
        video_url = f"https://youtube.com/watch?v={config['video_id']}"

        full_transcript = fetch_full_transcript(video_url)
        if full_transcript:
            print(f"[video_select] Fetched transcript for Week {week_number}: {len(full_transcript)} entries")
        else:
            print(f"[video_select] No transcript available - questions will use topic-based reasoning")

        for day_name, (day_start, day_end) in zip(all_days, per_day_segments):
            start_seconds = _timestamp_to_seconds(day_start)
            end_seconds = _timestamp_to_seconds(day_end) if day_end else start_seconds + 3600
            segment_text = extract_segment_text(full_transcript, start_seconds, end_seconds) if full_transcript else ""

            supabase.table("weekly_plan").insert({
                "week_number": week_number,
                "day_of_week": day_name,
                "topic": config.get("topic", topic),
                "video_url": video_url,
                "video_start_time": day_start,
                "video_end_time": day_end,
                "channel_id": None,
                "channel_name": config.get("channel", ""),
                "status": "selected",
                "transcript_segment": segment_text[:3000] if segment_text else None
            }).execute()

    elif config["type"] == "episodes":
        episodes = config.get("episodes", [])
        days_to_use = all_days[:len(episodes)]

        for day_name, episode in zip(days_to_use, episodes):
            video_url = f"https://youtube.com/watch?v={episode['video_id']}"
            full_transcript = fetch_full_transcript(video_url)
            segment_text = ""
            if full_transcript:
                segment_text = extract_segment_text(full_transcript, 0, 99999)[:3000]

            supabase.table("weekly_plan").insert({
                "week_number": week_number,
                "day_of_week": day_name,
                "topic": config.get("topic", topic),
                "video_url": video_url,
                "video_start_time": "0:00:00",
                "video_end_time": None,
                "channel_id": None,
                "channel_name": config.get("channel", ""),
                "status": "selected",
                "transcript_segment": segment_text
            }).execute()

    print(f"[video_select] Week {week_number} saved using fixed map ({config['type']})")


def run_video_select():
    """
    Entry point - picks this week's video(s), determines timing, saves to
    weekly_plan for every day Monday-Saturday.
    For Weeks 1-12: uses the pre-verified fixed video map (real, confirmed
    sources - no YouTube search guesswork).
    For Weeks 13+: falls back to YouTube search-and-score pipeline (not yet
    verified, will be updated in a future session).
    """
    BROAD_WEEKS_SUB_TOPICS = {
        13: ["Docker basics fundamentals containers images", "Docker advanced multi-stage builds image optimization"],
        14: ["Kubernetes basics pods deployments services", "Kubernetes advanced autoscaling ingress production configuration"],
        16: ["Jenkins CI/CD pipeline fundamentals", "GitHub Actions CI/CD automation workflows"],
    }

    ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    week_number, topic = get_current_week_topic()

    # --- Weeks 1-12: use pre-verified fixed video map ---
    fixed_config = get_week_config(week_number)
    if fixed_config:
        print(f"[video_select] Week {week_number} using pre-verified fixed video source: {fixed_config.get('title', 'episode series')}")
        _save_fixed_week(week_number, topic, fixed_config, ALL_DAYS)
        return [fixed_config]

    # --- Weeks 13+: fall back to YouTube search pipeline ---
    print(f"[video_select] Week {week_number} not in fixed map yet - using search pipeline")

    sub_topics = BROAD_WEEKS_SUB_TOPICS.get(week_number)
    topics_to_search = sub_topics if sub_topics else [topic]

    saved_videos = []
    for i, search_topic in enumerate(topics_to_search):
        winner = pick_best_video(search_topic)

        if not winner:
            print(f"[video_select] No suitable video found for week {week_number} (part {i+1}): {search_topic}")
            continue

        duration_seconds = winner.get("duration_seconds")
        timing = extract_timestamp_range(winner.get("description", ""), search_topic, duration_seconds)
        saved_topic = search_topic if len(topics_to_search) > 1 else topic

        if len(topics_to_search) > 1:
            days_for_this_video = ALL_DAYS[:3] if i == 0 else ALL_DAYS[3:]
        else:
            days_for_this_video = ALL_DAYS

        has_timestamps = timing.get("has_timestamps", False)
        needs_split = timing.get("split_suggestion") is not None

        if not has_timestamps and needs_split and duration_seconds:
            per_day_segments = calculate_per_day_segments(duration_seconds, len(days_for_this_video))
        else:
            per_day_segments = [(timing.get("start_time", "0:00:00"), timing.get("end_time"))] * len(days_for_this_video)

        video_url = f"https://youtube.com/watch?v={winner['video_id']}"
        full_transcript = fetch_full_transcript(video_url)
        if full_transcript:
            print(f"[video_select] Fetched real transcript: {len(full_transcript)} entries")
        else:
            print(f"[video_select] No transcript available - will fall back to reasoning-based generation")

        for day_name, (day_start, day_end) in zip(days_for_this_video, per_day_segments):
            start_seconds = _timestamp_to_seconds(day_start)
            end_seconds = _timestamp_to_seconds(day_end) if day_end else start_seconds + 3600
            segment_text = extract_segment_text(full_transcript, start_seconds, end_seconds) if full_transcript else ""

            supabase.table("weekly_plan").insert({
                "week_number": week_number,
                "day_of_week": day_name,
                "topic": saved_topic,
                "video_url": video_url,
                "video_start_time": day_start,
                "video_end_time": day_end,
                "channel_id": winner["channel_id"],
                "channel_name": winner["channel_name"],
                "status": "selected",
                "transcript_segment": segment_text[:3000] if segment_text else None
            }).execute()

        part_label = f" (part {i+1}/{len(topics_to_search)})" if len(topics_to_search) > 1 else ""
        print(f"[video_select] Selected{part_label}: {winner['title']} ({winner['channel_name']}) - score: {winner['score']}, pbc_depth: {winner.get('pbc_depth')}, duration: {duration_seconds}s")
        saved_videos.append(winner)

    return saved_videos
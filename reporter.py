import os
from datetime import datetime
from db_client import supabase
import requests

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")


def get_today_quiz_status() -> dict:
    """Checks today's quiz performance from the scores table."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("scores").select("*").gte("created_at", today_start).order("created_at", desc=True).execute()

    if not result.data:
        return {"status": "not attempted", "detail": ""}

    latest = result.data[0]
    if latest.get("passed"):
        return {"status": "✅ passed", "detail": f"{latest.get('topic', 'topic')} - Gate1: {latest.get('gate1_score')}, Gate2: {latest.get('gate2_score')}"}
    else:
        return {"status": "⚠️ attempted, not passed", "detail": f"{latest.get('topic', 'topic')} - Gate1: {latest.get('gate1_score')}"}


def get_this_week_video() -> dict:
    """Checks this week's selected video from weekly_plan."""
    result = supabase.table("weekly_plan").select("*").order("created_at", desc=True).limit(1).execute()
    if not result.data:
        return {"status": "not selected", "detail": ""}
    row = result.data[0]
    return {"status": "✅ selected", "detail": f"{row.get('topic', 'topic')} - {row.get('channel_name', 'unknown channel')}"}


def get_today_job_scan_status() -> dict:
    """Checks if job scan ran today and found anything."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("jobs").select("*").gte("found_at", today_start).execute()

    if not result.data:
        return {"status": "✅ ran, no new matches found", "detail": ""}
    
    surfaced = [r for r in result.data if r.get("surfaced")]
    if surfaced:
        return {"status": f"✅ {len(surfaced)} new match(es)", "detail": ", ".join([f"{r['company']}" for r in surfaced[:3]])}
    else:
        return {"status": f"{len(result.data)} found, not yet surfaced (readiness gate)", "detail": ""}


def get_today_resume_score() -> dict:
    """Checks if resume ATS ran today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("resume_scores").select("*").gte("created_at", today_start).order("created_at", desc=True).limit(1).execute()

    if not result.data:
        return {"status": "not run today", "detail": ""}
    row = result.data[0]
    return {"status": f"{row.get('score')}/100", "detail": row.get("feedback", "")[:100]}


def build_daily_report() -> str:
    """Assembles the full daily report from all module results."""
    quiz = get_today_quiz_status()
    video = get_this_week_video()
    jobs = get_today_job_scan_status()
    resume = get_today_resume_score()

    report = f"""📋 **JARVIS Daily Report** - {datetime.utcnow().strftime('%B %d, %Y')}

**📚 Quiz:** {quiz['status']}
{quiz['detail']}

**🎥 This Week's Video:** {video['status']}
{video['detail']}

**💼 Job Scan:** {jobs['status']}
{jobs['detail']}

**📄 Resume ATS:** {resume['status']}
{resume['detail']}
"""
    return report


def post_to_discord(message: str):
    """Posts the report to the JARVIS Discord channel via webhook."""
    if not DISCORD_WEBHOOK:
        print("[reporter] No Discord webhook configured, printing instead:")
        print(message)
        return

    try:
        response = requests.post(DISCORD_WEBHOOK, json={"content": message})
        if response.status_code not in (200, 204):
            print(f"[reporter] Discord post failed: {response.status_code} - {response.text}")
        else:
            print("[reporter] Report posted successfully")
    except Exception as e:
        print(f"[reporter] Error posting to Discord: {e}")


def run_reporter():
    """Entry point - builds and posts today's report."""
    report = build_daily_report()
    post_to_discord(report)
    return report

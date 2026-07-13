"""
daily_task.py - Sends daily task list to Discord every morning
Runs via EventBridge after video_select.py generates the day's content
"""

import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JARVIS_URL = "https://32.198.23.203"

def get_today_plan():
    """Get today's video segment from Supabase."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = now_ist.strftime("%A")

    url = f"{SUPABASE_URL}/rest/v1/weekly_plan?day_of_week=eq.{today}&order=created_at.desc&limit=1"
    res = requests.get(url, headers=headers)
    data = res.json()
    return data[0] if data else None

def get_pending_interviews():
    """Check if interview questions are pending."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/interview_sessions?score=is.null&limit=3"
    res = requests.get(url, headers=headers)
    data = res.json()
    return len(data) if data else 0

def get_quiz_scores():
    """Get recent quiz performance."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/scores?order=created_at.desc&limit=10"
    res = requests.get(url, headers=headers)
    data = res.json()
    if not data:
        return None, 0
    scores = [r.get("gate1_score") for r in data if r.get("gate1_score")]
    avg = round(sum(scores)/len(scores), 1) if scores else 0
    return avg, len(data)

def get_weak_areas():
    """Get weak concepts from knowledge_state."""
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    url = f"{SUPABASE_URL}/rest/v1/knowledge_state?mastery_score=lt.0.7&order=mastery_score&limit=3"
    res = requests.get(url, headers=headers)
    data = res.json()
    return [r["concept"] for r in data] if data else []

def send_daily_tasks():
    """Send daily task list to Discord."""
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = now_ist.strftime("%A")
    date_str = now_ist.strftime("%B %d, %Y")

    plan = get_today_plan()
    pending_interviews = get_pending_interviews()
    avg_score, total_sessions = get_quiz_scores()
    weak_areas = get_weak_areas()

    # Determine week number
    week_num = plan.get("week_number", 1) if plan else 1
    topic = plan.get("topic", "Linux Basics").split("-")[0].strip() if plan else "Linux Basics"
    start_time = plan.get("video_start_time", "0:00:00") if plan else "0:00:00"
    end_time = plan.get("video_end_time", "") if plan else ""
    video_url = plan.get("video_url", "") if plan else ""

    # Build task list based on day
    tasks = []

    if today == "Saturday":
        tasks = [
            f"🎤 Answer {pending_interviews} pending interview questions" if pending_interviews > 0 else "🎤 No pending interview questions",
            "💻 Code Practice: Open /code-page and do 2 exercises",
            f"⚡ Brain Mode: Chaos Question ({topic})",
            f"🐛 Brain Mode: Live Debug ({topic})",
            "🏗️ Brain Mode: PayFlow Drill (defend your architecture)"
        ]
    elif today == "Sunday":
        tasks = [
            "🔧 Hands-on: Killercoda Linux Labs",
            "🔧 Hands-on: HackerRank Shell Practice",
            "🚀 PayFlow: Work on this week's project tasks",
            f"🎯 Brain Mode: Readiness Score (Week {week_num} assessment)",
            "📊 Brain Mode: SLO Design practice"
        ]
    else:
        # Weekday
        tasks = [
            f"📹 Watch: {topic} ({start_time} → {end_time})" + (f"\n   {video_url}" if video_url else ""),
            "📝 Answer 6 quiz questions AFTER watching",
            f"⚡ Brain Mode: Chaos Question ({topic})",
            f"🐛 Brain Mode: Live Debug ({topic})",
        ]
        if today == "Friday":
            tasks.append("🎤 Interview questions will be auto-generated today")

    # Add spaced repetition reminder
    if weak_areas:
        tasks.append(f"🔁 Spaced Review: {', '.join(weak_areas[:2])} (flagged weak)")

    # Build Discord message
    tasks_text = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])

    score_text = f"• Avg Score: {avg_score}/10 ({total_sessions} sessions)" if avg_score else "• Avg Score: No sessions yet"
    weak_text = f"• Weak Areas: {', '.join(weak_areas)}" if weak_areas else "• Weak Areas: None identified yet"

    message = f"""━━━━━━━━━━━━━━━━━━━━━━━
⚡ **JARVIS — {today} {date_str}**
📚 Week {week_num} · {topic}
━━━━━━━━━━━━━━━━━━━━━━━

**🎯 TODAY'S TASKS:**
{tasks_text}

**📊 YOUR STATUS:**
{score_text}
{weak_text}
- Target: Mid-level DevOps/Platform Engineer by Oct 2026

**💬 Open JARVIS:** {JARVIS_URL}/chat
━━━━━━━━━━━━━━━━━━━━━━━"""

    # Send to Discord
    if DISCORD_WEBHOOK:
        payload = {"content": message}
        res = requests.post(DISCORD_WEBHOOK, json=payload)
        if res.status_code in [200, 204]:
            print("[daily_task] Discord message sent successfully")
        else:
            print(f"[daily_task] Discord error: {res.status_code} {res.text}")
    else:
        print("[daily_task] No webhook configured")
        print(message)

if __name__ == "__main__":
    send_daily_tasks()

import random

FAILURE_DRILLS = [
    {
        "title": "P0 INCIDENT — Payment Service Down",
        "scenario": "Razorpay alert: 15,000 transactions/min failing. Payment pods in CrashLoopBackOff. Error rate 94%.",
        "task": "You are on-call. 10 minutes. What do you do first?"
    },
    {
        "title": "P1 INCIDENT — Database Connection Pool Exhausted", 
        "scenario": "Swiggy alert: PostgreSQL max_connections reached. Orders stalling. API latency 45 seconds. 50,000 users affected.",
        "task": "What is your first command and why?"
    },
    {
        "title": "P0 INCIDENT — Kubernetes Node NotReady",
        "scenario": "PhonePe alert: 3 of 5 EKS nodes NotReady. Pods evicting. UPI service degraded. RBI SLA breach in 8 minutes.",
        "task": "What do you check first?"
    },
    {
        "title": "P1 INCIDENT — CI/CD Pipeline Blocked",
        "scenario": "CRED alert: GitHub Actions failing all PRs. ArgoCD sync stuck. Critical hotfix cannot deploy.",
        "task": "Unblock the pipeline. What is your immediate diagnosis?"
    },
    {
        "title": "P0 INCIDENT — Disk Space Critical",
        "scenario": "Groww alert: /var/log at 99%. Nginx log rotation failed. Service writes failing silently.",
        "task": "5 minutes before service goes down. What do you do?"
    }
]

def send_failure_drill():
    """Send random production incident drill to Discord."""
    from datetime import datetime, timedelta
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    hour = now_ist.hour
    if not (10 <= hour <= 20):
        return
    if random.random() > 0.3:
        return
    drill = random.choice(FAILURE_DRILLS)
    message = f"""
🚨🚨🚨 **JARVIS FAILURE DRILL** 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━

**{drill['title']}**

{drill['scenario']}

⏱️ **YOUR TASK:** {drill['task']}

*Training drill — respond with your incident steps*
━━━━━━━━━━━━━━━━━━━━━━━"""
    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
        print("[daily_task] Failure drill sent to Discord")

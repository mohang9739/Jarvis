import os
import requests
from datetime import datetime, timedelta
from db_client import supabase

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')

def get_ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def get_today_plan():
    now = get_ist_now()
    today = now.strftime('%A')
    
    # Get current week (July 28 = Week 1 Day 1)
    start_date = datetime(2026, 7, 28)
    days_passed = (now - start_date).days
    week_number = min(8, max(1, (days_passed // 7) + 1))
    
    result = supabase.table('weekly_plan').select('*').eq('week_number', week_number).eq('day_of_week', today).execute()
    return result.data[0] if result.data else None

def get_break_fix():
    now = get_ist_now()
    today = now.strftime('%A')
    start_date = datetime(2026, 7, 28)
    days_passed = (now - start_date).days
    week_number = min(8, max(1, (days_passed // 7) + 1))
    
    result = supabase.table('jarvis_break_fix').select('*').eq('week_number', week_number).eq('day_of_week', today).execute()
    return result.data[0] if result.data else None

def get_sunday_task():
    now = get_ist_now()
    start_date = datetime(2026, 7, 28)
    days_passed = (now - start_date).days
    week_number = min(8, max(1, (days_passed // 7) + 1))
    
    result = supabase.table('jarvis_sunday_tasks').select('*').eq('week_number', week_number).execute()
    return result.data[0] if result.data else None

def send_daily_message():
    now = get_ist_now()
    today = now.strftime('%A')
    date_str = now.strftime('%B %d, %Y')
    
    # Sunday = project build day
    if today == 'Sunday':
        task = get_sunday_task()
        if not task:
            return
            
        message = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 SUNDAY BUILD DAY — {date_str}
━━━━━━━━━━━━━━━━━━━━━━━━━

📁 **{task['task_title']}**
{task['description']}

⏱️ Estimated time: {task['estimated_time']}

✅ **DONE WHEN:**
{task['done_when']}

📋 **STEPS:**
{task['steps'][:1500]}

🎯 **NEXT SUNDAY:**
{task['next_sunday']}
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    else:
        plan = get_today_plan()
        break_fix = get_break_fix()
        
        if not plan:
            return
            
        start_date = datetime(2026, 7, 28)
        days_passed = (now - start_date).days
        week_number = min(8, max(1, (days_passed // 7) + 1))
        
        message = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
☀️ JARVIS DAILY BRIEF — {date_str}
━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Week {week_number} | {today}
🎯 Azure Cloud Engineer Journey

📹 **TODAY'S STUDY (9 AM - 12 PM)**
Topic: {plan['topic']}
Video: {plan['video_url']}
Segment: {plan['video_start_time']} → {plan['video_end_time']}
Channel: {plan['channel_name']}

⏰ **SCHEDULE**
9:00 - 10:00 AM → Watch video segment
10:00 - 11:00 AM → Hands-on Azure portal
11:00 - 12:00 PM → Interview speaking practice

🔧 **BREAK-FIX SCENARIO**"""

        if break_fix:
            message += f"""
Scenario: {break_fix['scenario_title']}
Break: `{break_fix['break_command'][:100]}`
Symptom: {break_fix['symptom']}
Fix: `{break_fix['fix_command'][:100]}`
Why: {break_fix['explanation']}"""
        
        message += f"""

💬 **INTERVIEW PRACTICE (Hour 3)**
Practice saying out loud:
"I am an Azure Cloud Infrastructure Engineer
with 4.6 years at Accenture. I hold AZ-140
and AI-102 certifications. I built an Azure
Infrastructure Automation Suite using Terraform
that reduces AVD provisioning from 4 hours
to 18 minutes."

🔥 **SIGNATURE LINE (memorize)**
"Reduced AVD provisioning from 4+ hours
to 18 minutes using Terraform automation"

📊 **PROGRESS**
Week {week_number}/8 | {today}
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    if DISCORD_WEBHOOK:
        requests.post(DISCORD_WEBHOOK, json={'content': message})
        print(f'Daily message sent - {today}')
    else:
        print(message)

if __name__ == '__main__':
    send_daily_message()

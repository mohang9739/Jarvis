import os
from datetime import datetime, timedelta
from supabase import create_client
from ai_client import ask_ai_json, ask_ai

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

USER_STATS = {
    "weight_kg": 84,
    "height_cm": 171,
    "target_weight_kg": 76,
    "target_pace_kg_per_week": 0.6
}


def get_current_shift():
    result = supabase.table("current_shift").select("*").execute()
    if result.data:
        return result.data[0]["shift_type"]
    return "night"


def get_active_symptoms():
    result = supabase.table("symptom_log").select("*").eq("active", True).execute()
    return [row["symptom"] for row in result.data] if result.data else []


def get_weight_trend():
    cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
    result = supabase.table("weight_log").select("*").gte("logged_at", cutoff).order("logged_at").execute()
    return result.data if result.data else []


def get_today_meals():
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("meal_log").select("*").gte("logged_at", today_start).execute()
    return result.data if result.data else []


def get_today_study_status():
    """Checks if today's quiz was completed, attempted but not passed, or not attempted yet."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("scores").select("*").gte("created_at", today_start).order("created_at", desc=True).limit(1).execute()
    if not result.data:
        return "pending"
    latest = result.data[0]
    return "completed" if latest.get("passed") else "attempted_not_passed"


def build_context():
    shift = get_current_shift()
    symptoms = get_active_symptoms()
    weight_trend = get_weight_trend()
    today_meals = get_today_meals()
    study_status = get_today_study_status()
    total_cal_today = sum(m.get("calories", 0) or 0 for m in today_meals)

    return {
        "shift": shift,
        "active_symptoms": symptoms,
        "weight_trend": weight_trend,
        "today_meals_logged": len(today_meals),
        "calories_logged_today": total_cal_today,
        "study_status": study_status,
        "stats": USER_STATS
    }


def get_walk_suggestion():
    """Suggests the best walk window today based on shift + study status + meal timing."""
    context = build_context()
    today_meals = get_today_meals()
    meal_summary = "; ".join(
        [f"{m.get('meal_type', 'meal')} at {m.get('logged_at', '')[11:16]}" for m in today_meals]
    ) or "no meals logged yet today"

    prompt = f"""
Suggest the single best 30-minute window today for a walk, for someone trying to lose weight sustainably.

Current shift: {context['shift']}
Today's study status: {context['study_status']}
Meals logged today: {meal_summary}

Shift timing reference:
- morning shift: 6 AM-3 PM
- afternoon shift: 2 PM-11 PM
- night shift: 10 PM-7 AM

Reasoning:
- Prefer a walk 30-60 minutes AFTER a meal, not immediately after or on an empty stomach right before one
- If study is still pending, suggest a window that does not conflict with when they would likely study
- If study is completed, suggest a relaxed window, e.g. right after the shift ends
- If study was deferred/skipped, do not reference a study block that is not happening today

Keep the response to 1-2 short sentences - just the window and one line of reasoning.
"""
    return ask_ai(prompt)
import os
from datetime import datetime, timedelta
from supabase import create_client
from ai_client import ask_ai_json

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

def build_context():
    shift = get_current_shift()
    symptoms = get_active_symptoms()
    weight_trend = get_weight_trend()
    today_meals = get_today_meals()
    total_cal_today = sum(m.get("calories", 0) or 0 for m in today_meals)

    return {
        "shift": shift,
        "active_symptoms": symptoms,
        "weight_trend": weight_trend,
        "today_meals_logged": len(today_meals),
        "calories_logged_today": total_cal_today,
        "stats": USER_STATS
    }

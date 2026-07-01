import os
from datetime import datetime
from supabase import create_client
from ai_client import ask_ai_json
from health_engine import build_context

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def handle_meal(user_message: str) -> dict:
    """
    Handles /meal command. Distinguishes between:
    - "thinking of eating X" -> AI can push back with an alternative
    - "only have X" -> AI accepts constraint, plans rest of day around it
    """
    context = build_context()

    prompt = f"""
You are a food/weight coach for someone actively trying to lose weight sustainably.

Their stats: {context['stats']}
Current shift: {context['shift']}
Active health symptoms right now: {context['active_symptoms'] or 'none'}
Calories logged so far today: {context['calories_logged_today']}
Recent weight trend (last 7 days): {context['weight_trend']}

They just said: "{user_message}"

First, determine if this is:
(a) A CHOICE being floated - they're considering eating something, open to alternatives
(b) A CONSTRAINT being stated - this is genuinely all that's available, no alternative exists

If (a) and the food isn't ideal given their goals, suggest a better alternative if one is realistic.
If (b), accept it, estimate its calories/protein, and adjust guidance for their REMAINING meals today
to balance out the day's total.

If they mentioned any symptom (stomach issues, etc.), factor that into food safety, not just calories.

Return JSON with exactly these fields:
{{
  "is_constraint": <true or false>,
  "meal_type": "<breakfast/lunch/dinner/snack, inferred or unspecified>",
  "food_items": "<what they mentioned>",
  "calories": <estimated integer>,
  "response": "<your actual advice to them, 2-4 sentences, conversational>"
}}
"""
    result = ask_ai_json(prompt)

    supabase.table("meal_log").insert({
        "meal_type": result.get("meal_type", "unspecified"),
        "food_items": result.get("food_items", user_message),
        "calories": result.get("calories", 0),
        "ai_feedback": result.get("response", ""),
        "is_constraint": result.get("is_constraint", False)
    }).execute()

    return result

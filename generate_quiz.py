"""Generates daily quiz questions from today's transcript and saves to Supabase."""
from ai_client import ask_ai
from db_client import supabase
from datetime import datetime, timedelta
import json, re

def generate_daily_quiz():
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = now_ist.strftime("%A")

    plan = supabase.table("weekly_plan").select("topic,transcript_segment").eq(
        "day_of_week", today).order("created_at", desc=True).limit(1).execute()

    if not plan.data or not plan.data[0].get("transcript_segment"):
        print("[quiz_gen] No transcript found for today")
        return

    topic = plan.data[0]["topic"]
    transcript = plan.data[0]["transcript_segment"]

    # Check if questions already generated today
    # Always regenerate if called after transcript save
    import sys
    force = '--force' in sys.argv
    existing = supabase.table("quiz_sessions").select("id").eq(
        "topic", topic).eq("status", "pending").execute()
    if existing.data and not force:
        print(f"[quiz_gen] Questions already exist for {topic}")
        return
    elif existing.data and force:
        supabase.table("quiz_sessions").delete().eq("topic", topic).eq("status", "pending").execute()
        print(f"[quiz_gen] Cleared old questions, regenerating from real transcript")

    prompt = f"""Generate 6 quiz questions based on this Linux tutorial content.
Topic: {topic}
Content: {transcript[:2000]}

Questions should test genuine understanding, not memorization.
Mix: conceptual questions, scenario questions, command questions.
Return ONLY raw JSON array, no markdown:
[{{"question_text": "...", "correct_answer": "..."}}]"""

    result = ask_ai(prompt)
    clean = re.sub(r'```json|```', '', result).strip()

    try:
        questions = json.loads(clean)
        for i, q in enumerate(questions[:6]):
            supabase.table("quiz_sessions").insert({
                "topic": topic,
                "question_text": q.get("question_text", ""),
                "correct_answer": q.get("correct_answer", ""),
                "gate_number": 1,
                "status": "pending"
            }).execute()
        print(f"[quiz_gen] Generated {min(6,len(questions))} questions for {topic}")
    except Exception as e:
        print(f"[quiz_gen] Error: {e}")

if __name__ == "__main__":
    generate_daily_quiz()

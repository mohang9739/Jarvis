import os
from datetime import datetime
from supabase import create_client
from ai_client import ask_ai_json

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def grade_explain_back(topic: str, user_explanation: str) -> dict:
    """
    Gate 1: grades the user's own explanation of a topic.
    Must score >=7 to pass and unlock Gate 2.
    """
    prompt = f"""
You are grading a student's understanding of a technical topic for a DevOps/Platform Engineer interview prep system.

Topic: {topic}

Student's explanation, in their own words:
\"\"\"{user_explanation}\"\"\"

Grade this explanation on a scale of 1-10 for genuine understanding — not whether it uses the right vocabulary,
but whether it shows the student actually understands WHY the concept works, not just WHAT it is.
A vague or memorized-sounding answer should score low even if it uses correct terms.

Return JSON with exactly these fields:
{{
  "score": <integer 1-10>,
  "passed": <true if score >= 7, else false>,
  "feedback": "<2-3 sentences: what was good, what was missing or unclear>"
}}
"""
    result = ask_ai_json(prompt)

    supabase.table("scores").insert({
        "topic": topic,
        "gate1_score": result["score"],
        "gate1_feedback": result["feedback"],
        "passed": result["passed"]
    }).execute()

    return result


def generate_mcq(topic: str, difficulty: str = "medium") -> dict:
    """
    Gate 2: generates a fresh multiple-choice question for the topic.
    Only called after Gate 1 is passed.
    """
    prompt = f"""
Generate one multiple-choice question testing practical understanding of: {topic}

Difficulty: {difficulty}
This is for DevOps/Platform Engineer interview prep — scenario-based, not pure definition recall.

Return JSON with exactly these fields:
{{
  "question": "<the question text>",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "correct_answer": "<A, B, C, or D>",
  "explanation": "<1-2 sentences on why the correct answer is right>"
}}
"""
    return ask_ai_json(prompt)


def check_mcq_answer(question_data: dict, user_answer: str) -> bool:
    return user_answer.strip().upper() == question_data["correct_answer"].strip().upper()


def update_gate2_result(topic: str, score_percent: int):
    passed = score_percent >= 70
    supabase.table("scores").update({
        "gate2_score": score_percent,
        "passed": passed
    }).eq("topic", topic).order("created_at", desc=True).limit(1).execute()
    return passed

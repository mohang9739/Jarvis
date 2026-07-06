"""
JARVIS Quiz Engine
- Gate 1: Explain-Back → Gemini grades (≥7 pass, <7 retry with Stuck-Point loop)
- Gate 2: MCQ A/B/C/D → ≥70% pass, <70% Gemini explains weak areas + retry
- All interaction via Discord webhook
- Scores written to Supabase scores table
- Both gates are now scoped to TODAY'S ACTUAL VIDEO SEGMENT (video_start_time to
  video_end_time), not the full broad topic - since long videos get split across
  multiple days, testing the entire topic on Day 1 (after only the first segment)
  would unfairly cover material not yet watched.
"""

import os
import json
import time
import requests
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from supabase import create_client

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_client import ask_ai, ask_ai_json

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")

GATE1_PASS_SCORE = 7
GATE2_PASS_PERCENT = 70
MCQ_COUNT = 5
MAX_GATE1_RETRIES = 3
MAX_GATE2_RETRIES = 3
DISCORD_POLL_INTERVAL = 10
DISCORD_TIMEOUT = 300


def post_to_discord(message: str):
    payload = {"content": message}
    resp = requests.post(DISCORD_WEBHOOK, json=payload)
    if resp.status_code not in (200, 204):
        print(f"[quiz_engine] Discord post failed: {resp.status_code} {resp.text}")
    else:
        print(f"[quiz_engine] Discord posted: {message[:80]}...")


def wait_for_discord_reply(prompt_message: str, timeout: int = DISCORD_TIMEOUT) -> str:
    if prompt_message:
        post_to_discord(prompt_message)

    reply_file = "/tmp/jarvis_reply.txt"
    if os.path.exists(reply_file):
        os.remove(reply_file)

    print(f"[quiz_engine] Waiting for Discord reply (timeout: {timeout}s)...")
    elapsed = 0
    while elapsed < timeout:
        if os.path.exists(reply_file):
            with open(reply_file, "r") as f:
                reply = f.read().strip()
            os.remove(reply_file)
            print(f"[quiz_engine] Got reply: {reply[:80]}")
            return reply
        time.sleep(DISCORD_POLL_INTERVAL)
        elapsed += DISCORD_POLL_INTERVAL

    raise TimeoutError("No Discord reply received within timeout.")


def get_todays_topic() -> dict:
    from datetime import datetime, timedelta
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    today = now_ist.strftime("%A")
    result = supabase.table("weekly_plan").select("*").eq("day_of_week", today).order("created_at", desc=True).limit(1).execute()
    if not result.data:
        raise ValueError(f"No topic found for {today} in weekly_plan.")
    return result.data[0]


def build_segment_note(plan: dict) -> str:
    """
    Builds a note describing TODAY'S actual video segment (start-end time),
    so Gate 1 and Gate 2 can scope their questions to only what's genuinely
    been covered so far, not the entire broad topic regardless of progress.
    """
    start = plan.get("video_start_time")
    end = plan.get("video_end_time")

    if not start or not end:
        return ""

    return (
        f"\nIMPORTANT SCOPE NOTE: The learner has only watched from {start} to {end} of "
        f"today's video segment (this is one part of a longer video split across multiple "
        f"days). ONLY ask about concepts realistically covered within this specific segment - "
        f"do NOT ask about material that would only appear later in the full video, since "
        f"they have not reached that part yet.\n"
    )


def save_score(topic: str, gate1_score: int, gate1_feedback: str,
               gate2_score: int, passed: bool):
    supabase.table("scores").insert({
        "topic": topic,
        "gate1_score": gate1_score,
        "gate1_feedback": gate1_feedback,
        "gate2_score": gate2_score,
        "passed": passed,
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    print(f"[quiz_engine] Score saved: Gate1={gate1_score} Gate2={gate2_score} Passed={passed}")


def grade_gate1(topic: str, user_explanation: str, segment_note: str = "") -> dict:
    prompt = f"""
You are JARVIS, a strict but fair Platform Engineering tutor.

Topic: {topic}
{segment_note}
The learner explained it as:
\"\"\"{user_explanation}\"\"\"

Grade their explanation on a scale of 1-10 based on:
- Accuracy (is it technically correct?)
- Completeness (did they cover the key points genuinely reachable within today's segment?)
- Clarity (is it explained in their own words, not memorized?)

Be honest. Do NOT rubber-stamp a good score if the explanation is vague or wrong.

Respond ONLY with valid JSON:
{{
  "score": <integer 1-10>,
  "feedback": "<specific feedback on what was good, what was missing, what was wrong>",
  "key_points_missed": ["<point1>", "<point2>"]
}}
"""
    return ask_ai_json(prompt)


def stuck_point_reexplain(topic: str, key_points_missed: list) -> str:
    missed = "\n".join(f"- {p}" for p in key_points_missed)
    prompt = f"""
You are JARVIS. The learner is struggling with: {topic}

They missed these key points:
{missed}

Re-explain ONLY these missed points using a completely different angle:
- Use a real-world analogy
- Keep it under 150 words
- Make it stick

Do NOT repeat the same explanation they already saw.
"""
    return ask_ai(prompt)


def run_gate1(topic: str, segment_note: str = "") -> tuple:
    post_to_discord(
        f"🧠 **JARVIS — Gate 1: Explain-Back**\n\n"
        f"📌 **Today's Topic:** {topic}\n\n"
        f"Explain what **{topic}** means in your own words.\n"
        f"Type your explanation here 👇"
    )

    for attempt in range(1, MAX_GATE1_RETRIES + 1):
        if attempt > 1:
            user_explanation = wait_for_discord_reply(
                f"⏳ Attempt {attempt}/{MAX_GATE1_RETRIES} — Type your explanation 👇"
            )
        else:
            user_explanation = wait_for_discord_reply("")

        result = grade_gate1(topic, user_explanation, segment_note)
        score = result.get("score", 0)
        feedback = result.get("feedback", "")
        key_points_missed = result.get("key_points_missed", [])

        if score >= GATE1_PASS_SCORE:
            post_to_discord(
                f"✅ **Gate 1 Passed!** Score: {score}/10\n\n"
                f"📝 Feedback: {feedback}\n\n"
                f"🔓 Unlocking Gate 2..."
            )
            return score, feedback
        else:
            if attempt < MAX_GATE1_RETRIES:
                re_explanation = stuck_point_reexplain(topic, key_points_missed)
                post_to_discord(
                    f"❌ **Score: {score}/10** — Not quite yet.\n\n"
                    f"📝 {feedback}\n\n"
                    f"🔄 **JARVIS Re-explains:**\n{re_explanation}\n\n"
                    f"Try again 👇"
                )
            else:
                post_to_discord(
                    f"⚠️ **Gate 1 — Final attempt. Score: {score}/10**\n\n"
                    f"📝 {feedback}\n\n"
                    f"Moving to Gate 2 — review the weak points above."
                )
                return score, feedback

    return 0, "Max retries reached."


def generate_mcq(topic: str, count: int = MCQ_COUNT, segment_note: str = "") -> list:
    prompt = f"""
You are JARVIS. Generate {count} multiple-choice questions for a Platform Engineering interview on: {topic}
{segment_note}
Rules:
- Questions must test real understanding, not just definitions
- ONLY test material realistically covered within today's specific segment noted above (if any)
- Each question has exactly 4 options: A, B, C, D
- Only one correct answer per question
- Mix conceptual and practical questions

Respond ONLY with valid JSON array:
[
  {{
    "question": "<question text>",
    "options": {{
      "A": "<option A>",
      "B": "<option B>",
      "C": "<option C>",
      "D": "<option D>"
    }},
    "correct": "<A or B or C or D>",
    "explanation": "<why this is correct>"
  }}
]
"""
    return ask_ai_json(prompt)


def run_gate2(topic: str, segment_note: str = "") -> int:
    for attempt in range(1, MAX_GATE2_RETRIES + 1):
        post_to_discord(
            f"📋 **JARVIS — Gate 2: MCQ** (Attempt {attempt}/{MAX_GATE2_RETRIES})\n\n"
            f"Generating {MCQ_COUNT} questions on **{topic}**..."
        )

        questions = generate_mcq(topic, segment_note=segment_note)
        correct_count = 0
        wrong_questions = []

        for i, q in enumerate(questions, 1):
            question_text = (
                f"**Q{i}/{MCQ_COUNT}:** {q['question']}\n\n"
                f"🅐 {q['options']['A']}\n"
                f"🅑 {q['options']['B']}\n"
                f"🅒 {q['options']['C']}\n"
                f"🅓 {q['options']['D']}\n\n"
                f"Reply with A, B, C, or D"
            )

            user_answer = wait_for_discord_reply(question_text).upper().strip()

            if user_answer == q["correct"]:
                correct_count += 1
                post_to_discord(f"✅ Correct! {q['explanation']}")
            else:
                wrong_questions.append(q)
                post_to_discord(
                    f"❌ Incorrect. Correct answer: **{q['correct']}**\n"
                    f"📖 {q['explanation']}"
                )

        score_percent = int((correct_count / len(questions)) * 100)

        if score_percent >= GATE2_PASS_PERCENT:
            post_to_discord(
                f"🎉 **Gate 2 Passed!** Score: {score_percent}% ({correct_count}/{len(questions)})\n\n"
                f"✅ **Topic Unlocked:** {topic}\n"
                f"Tomorrow's content will load automatically."
            )
            return score_percent
        else:
            if attempt < MAX_GATE2_RETRIES:
                weak_str = "\n".join(f"- {q['question']}" for q in wrong_questions)
                prompt = f"""
You are JARVIS. The learner scored {score_percent}% on {topic} MCQ.

They got these wrong:
{weak_str}

Give a concise re-explanation (under 200 words) targeting ONLY their weak areas.
Use simple language and a real-world DevOps/Platform Engineering context.
"""
                re_explain = ask_ai(prompt)
                post_to_discord(
                    f"⚠️ **Score: {score_percent}%** — Need ≥70% to pass.\n\n"
                    f"🔄 **JARVIS explains your weak areas:**\n{re_explain}\n\n"
                    f"🔁 Retrying Gate 2..."
                )
            else:
                post_to_discord(
                    f"⚠️ **Gate 2 Final Score: {score_percent}%**\n\n"
                    f"Review the explanations above and revisit this topic tomorrow."
                )
                return score_percent

    return 0


def run_quiz():
    print("[quiz_engine] Starting...")
    try:
        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        plan = get_todays_topic()
        topic = plan["topic"]
        segment_note = build_segment_note(plan)
        print(f"[quiz_engine] Today's topic: {topic}, segment: {plan.get('video_start_time')}-{plan.get('video_end_time')}")

        post_to_discord(
            f"🚀 **JARVIS Quiz Starting**\n"
            f"📅 {now_ist.strftime('%A, %d %B %Y')}\n"
            
            f"📌 Topic: **{topic}**"
        )

        gate1_score, gate1_feedback = run_gate1(topic, segment_note)
        gate2_score = run_gate2(topic, segment_note)

        passed = gate1_score >= GATE1_PASS_SCORE and gate2_score >= GATE2_PASS_PERCENT
        save_score(topic, gate1_score, gate1_feedback, gate2_score, passed)

        print(f"[quiz_engine] Done. Gate1={gate1_score} Gate2={gate2_score}% Passed={passed}")

    except Exception as e:
        print(f"[quiz_engine] ERROR: {e}")
        post_to_discord(f"⚠️ **JARVIS Quiz Engine Error:** {e}")
        raise


if __name__ == "__main__":
    run_quiz()
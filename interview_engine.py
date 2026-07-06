from ai_client import ask_ai_json
from db_client import supabase


def get_weeks_transcript_content(week_number: int) -> str:
    """
    Pulls the real, actual transcript content saved for this week (across
    all its days in weekly_plan), combining it into one block of genuine
    spoken content to ground interview question generation - the same real
    content Quiz Engine now uses, rather than generic topic-based reasoning.
    """
    result = supabase.table("weekly_plan").select("transcript_segment").eq("week_number", week_number).execute()
    if not result.data:
        return ""

    segments = [row.get("transcript_segment") for row in result.data if row.get("transcript_segment")]
    combined = " ".join(segments)
    return combined[:6000]


def generate_interview_question(topic: str, question_type: str, transcript_content: str = "") -> dict:
    """
    Generates a fresh scenario/architecture/coding question scoped to the
    week's topic - grounded in REAL transcript content when available,
    so questions reference genuine concepts/commands actually covered in
    the video, not generic topic-based reasoning alone.
    """
    content_block = ""
    if transcript_content:
        content_block = f"""
REAL VIDEO CONTENT - this is genuine content actually covered this week:
\"\"\"
{transcript_content}
\"\"\"

Ground your question in SPECIFIC concepts, commands, or examples genuinely mentioned above where
possible, not generic reasoning about the topic in the abstract.
"""

    prompt = f"""
Generate ONE {question_type} interview question for a Platform Engineer/DevOps/SRE candidate,
scoped specifically to this week's topic: {topic}
{content_block}
This should be the kind of question asked at product-based companies like Razorpay, Swiggy, PhonePe -
real scenario reasoning, not textbook definition recall.

question_type options: "scenario" (a real incident/situation to reason through), "architecture"
(design/tradeoff reasoning), "coding" (write actual code/commands, not just describe).

Return JSON:
{{
  "question": "the actual question text",
  "question_type": "{question_type}"
}}
"""
    return ask_ai_json(prompt)


def grade_interview_answer(question: str, user_answer: str, topic: str) -> dict:
    """
    Grades an interview answer with real, honest, PBC-interview-level rigor -
    same grading discipline as Gate 1's Explain-Back, applied to interview
    depth rather than just conceptual understanding.
    """
    prompt = f"""
You are grading a Platform Engineer/DevOps interview answer with the rigor of a real PBC interviewer.

Topic: {topic}
Question: {question}
Candidate's answer: {user_answer}

Grade honestly on a scale of 1-10. A correct-but-shallow answer should NOT score highly - real interviews
probe depth, edge cases, and tradeoffs, not just surface correctness.

Return JSON:
{{
  "score": <1-10>,
  "feedback": "specific, honest feedback - what was strong, what was missing or shallow"
}}
"""
    return ask_ai_json(prompt)


def run_weekly_interview_set(week_number: int, topic: str, question_types=None):
    """
    Generates a full set of questions (scenario, architecture, coding) for
    the week's topic, grounded in the real transcript content saved across
    this week's days, saves the questions (unanswered) for the user to
    respond to later via Discord or the dashboard.
    """
    if question_types is None:
        question_types = ["scenario", "architecture", "coding"]

    transcript_content = get_weeks_transcript_content(week_number)
    if transcript_content:
        print(f"[interview_engine] Grounding questions in {len(transcript_content)} chars of real transcript content")
    else:
        print("[interview_engine] No transcript content available - using topic-based reasoning")

    created = []
    for q_type in question_types:
        q_data = generate_interview_question(topic, q_type, transcript_content)
        result = supabase.table("interview_sessions").insert({
            "week_number": week_number,
            "topic": topic,
            "question": q_data.get("question"),
            "question_type": q_type,
        }).execute()
        created.append(result.data[0] if result.data else None)

    return created


def submit_interview_answer(session_id: str, user_answer: str):
    """Grades and saves the answer for an existing interview_sessions row."""
    row = supabase.table("interview_sessions").select("*").eq("id", session_id).execute()
    if not row.data:
        return None

    session = row.data[0]
    grading = grade_interview_answer(session["question"], user_answer, session["topic"])

    supabase.table("interview_sessions").update({
        "user_answer": user_answer,
        "score": grading.get("score"),
        "feedback": grading.get("feedback")
    }).eq("id", session_id).execute()

    return grading
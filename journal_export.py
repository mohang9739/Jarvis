"""
Journal Export - pulls today's real quiz score, interview Q&A, and any
practice notes file, writes a clean markdown entry, commits and pushes to
the devops-learning-journal repo. Runs as part of the daily Orchestrator
sequence, fully automated - no manual git work required.
"""

import os
import subprocess
from datetime import datetime, timedelta
from db_client import supabase

JOURNAL_REPO_PATH = os.path.expanduser("~/devops-learning-journal")
PRACTICE_NOTES_PATH = os.path.expanduser("~/jarvis/practice_notes")


def get_todays_quiz_entry():
    """Pulls today's real quiz score from the scores table, if one exists."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("scores").select("*").gte("created_at", today_start).order("created_at", desc=True).limit(1).execute()
    if not result.data:
        return None
    return result.data[0]


def get_todays_interview_entries():
    """Pulls any interview sessions genuinely answered today."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0).isoformat()
    result = supabase.table("interview_sessions").select("*").gte("created_at", today_start).execute()
    return result.data if result.data else []


def get_practice_notes(date_str: str) -> str:
    """Reads today's practice notes file if it exists, otherwise returns empty."""
    file_path = os.path.join(PRACTICE_NOTES_PATH, f"{date_str}.md")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read().strip()
    return ""


def build_journal_entry(date_str: str) -> str:
    """Assembles the full markdown journal entry for today."""
    quiz = get_todays_quiz_entry()
    interviews = get_todays_interview_entries()
    practice = get_practice_notes(date_str)

    entry = f"# {date_str}\n\n"

    if quiz:
        entry += f"## Quiz Results\n\n"
        entry += f"**Topic:** {quiz.get('topic', 'N/A')}\n\n"
        entry += f"- Gate 1 (Explain-Back): {quiz.get('gate1_score')}/10\n"
        entry += f"- Gate 2 (MCQ): {quiz.get('gate2_score')}%\n"
        entry += f"- Result: {'Passed' if quiz.get('passed') else 'Not yet passed'}\n\n"
        if quiz.get("gate1_feedback"):
            entry += f"**Feedback:** {quiz.get('gate1_feedback')}\n\n"
    else:
        entry += "## Quiz Results\n\nNo quiz attempted today.\n\n"

    if interviews:
        entry += "## Interview Practice\n\n"
        for session in interviews:
            entry += f"### {session.get('question_type', 'question').title()}\n\n"
            entry += f"**Question:** {session.get('question', '')}\n\n"
            if session.get("user_answer"):
                entry += f"**My Answer:** {session.get('user_answer')}\n\n"
            if session.get("score") is not None:
                entry += f"**Score:** {session.get('score')}/10\n\n"
                entry += f"**Feedback:** {session.get('feedback', '')}\n\n"
    else:
        entry += "## Interview Practice\n\nNo interview questions answered today.\n\n"

    if practice:
        entry += f"## Hands-On Practice Notes\n\n{practice}\n\n"
    else:
        entry += "## Hands-On Practice Notes\n\n_No practice notes logged today._\n\n"

    return entry


def commit_and_push_journal(date_str: str, entry_content: str):
    """Writes the entry file, commits, and pushes to the journal repo."""
    entries_dir = os.path.join(JOURNAL_REPO_PATH, "entries")
    os.makedirs(entries_dir, exist_ok=True)

    entry_path = os.path.join(entries_dir, f"{date_str}.md")
    with open(entry_path, "w") as f:
        f.write(entry_content)

    try:
        subprocess.run(["git", "add", "."], cwd=JOURNAL_REPO_PATH, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"Daily entry: {date_str}"],
            cwd=JOURNAL_REPO_PATH, capture_output=True, text=True
        )
        if "nothing to commit" in result.stdout:
            print(f"[journal_export] No changes to commit for {date_str}")
            return
        subprocess.run(["git", "push", "origin", "master"], cwd=JOURNAL_REPO_PATH, check=True)
        print(f"[journal_export] Successfully pushed entry for {date_str}")
    except subprocess.CalledProcessError as e:
        print(f"[journal_export] Git operation failed: {e}")


def run_journal_export():
    """Entry point - builds and pushes today's journal entry."""
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    date_str = now_ist.strftime("%Y-%m-%d")

    entry = build_journal_entry(date_str)
    commit_and_push_journal(date_str, entry)
    return entry


if __name__ == "__main__":
    run_journal_export()

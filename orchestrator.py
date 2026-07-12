import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_select import run_video_select, get_current_week_topic
from job_scan import run_job_scan
from reporter import run_reporter
from interview_engine import run_weekly_interview_set
from journal_export import run_journal_export
from health_engine import get_current_shift, get_today_study_status
from daily_task import send_daily_tasks


def get_module_status_summary() -> dict:
    """Tracks which modules ran successfully today, for health visibility in the report."""
    return {
        "video_select": {"ran": False, "error": None},
        "interview_set": {"ran": False, "error": None},
        "job_scan": {"ran": False, "error": None},
        "reporter": {"ran": False, "error": None},
        "journal_export": {"ran": False, "error": None},
        "daily_task": {"ran": False, "error": None},
    }


def should_delay_report(shift: str, study_status: str) -> bool:
    """
    Determines if the report should be delayed rather than posted immediately.
    Currently used for logging/detection only.
    """
    now = datetime.utcnow()
    ist_hour = (now.hour + 5) % 24

    SLEEP_WINDOWS = {
        "morning": (22, 5),
        "afternoon": (1, 9),
        "night": (7, 13),
    }

    sleep_start, sleep_end = SLEEP_WINDOWS.get(shift, (7, 13))
    if sleep_start > sleep_end:
        is_sleep_time = ist_hour >= sleep_start or ist_hour < sleep_end
    else:
        is_sleep_time = sleep_start <= ist_hour < sleep_end

    return is_sleep_time


def run_daily_orchestration():
    """
    Entry point - runs the full daily JARVIS sequence.
    Video Select runs Monday only. Interview Set runs Friday only, testing
    AFTER a real week of studying. Job Scan and Reporter run daily. Journal
    Export runs daily last, automatically pushing real quiz/interview
    progress plus any practice notes to the devops-learning-journal repo -
    no manual git work required. Each module is wrapped independently so
    one failure doesn't block others.
    """
    status = get_module_status_summary()
    today = datetime.utcnow()
    is_monday = today.weekday() == 0
    is_friday = today.weekday() == 4

    shift = get_current_shift()
    study_status = get_today_study_status()
    print(f"[orchestrator] Starting daily run - shift: {shift}, study_status: {study_status}, Monday: {is_monday}, Friday: {is_friday}")

    if should_delay_report(shift, study_status):
        print(f"[orchestrator] Current time falls in {shift} shift's likely sleep window - report will still post, but this is logged for future scheduling refinement.")

    # --- Daily Task List: runs every day FIRST ---
    try:
        send_daily_tasks()
        status["daily_task"]["ran"] = True
        print("[orchestrator] Daily task list sent to Discord")
    except Exception as e:
        status["daily_task"]["error"] = str(e)
        print(f"[orchestrator] Daily task failed: {e}")

    # --- Video Select: Monday only ---
    if is_monday:
        try:
            run_video_select()
            status["video_select"]["ran"] = True
        except Exception as e:
            status["video_select"]["error"] = str(e)
            print(f"[orchestrator] Video Select failed: {e}")
    else:
        print("[orchestrator] Skipping Video Select - not Monday")

    # --- Interview Set: Friday only, testing AFTER a real week of studying ---
    if is_friday:
        try:
            week_number, topic = get_current_week_topic()
            run_weekly_interview_set(week_number, topic)
            status["interview_set"]["ran"] = True
            print(f"[orchestrator] Interview set generated for week {week_number}: {topic}")
        except Exception as interview_error:
            status["interview_set"]["error"] = str(interview_error)
            print(f"[orchestrator] Interview set generation failed: {interview_error}")
    else:
        print("[orchestrator] Skipping Interview Set - not Friday")

    # --- Job Scan: runs daily, but internally gates surfacing based on readiness ---
    try:
        run_job_scan()
        status["job_scan"]["ran"] = True
    except Exception as e:
        status["job_scan"]["error"] = str(e)
        print(f"[orchestrator] Job Scan failed: {e}")

    # --- Reporter: always runs, summarizes whatever happened, even partial failures ---
    try:
        run_reporter()
        status["reporter"]["ran"] = True
    except Exception as e:
        status["reporter"]["error"] = str(e)
        print(f"[orchestrator] Reporter failed: {e}")

    # --- Journal Export: pushes today's real quiz/interview data + practice notes automatically ---
    try:
        run_journal_export()
        status["journal_export"]["ran"] = True
    except Exception as e:
        status["journal_export"]["error"] = str(e)
        print(f"[orchestrator] Journal export failed: {e}")

    print(f"[orchestrator] Daily run complete. Status: {status}")
    return status


if __name__ == "__main__":
    run_daily_orchestration()
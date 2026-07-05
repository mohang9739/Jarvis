import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_select import run_video_select, get_current_week_topic
from job_scan import run_job_scan
from reporter import run_reporter
from interview_engine import run_weekly_interview_set
from health_engine import get_current_shift, get_today_study_status


def get_module_status_summary() -> dict:
    """Tracks which modules ran successfully today, for health visibility in the report."""
    return {
        "video_select": {"ran": False, "error": None},
        "interview_set": {"ran": False, "error": None},
        "job_scan": {"ran": False, "error": None},
        "reporter": {"ran": False, "error": None},
    }


def should_delay_report(shift: str, study_status: str) -> bool:
    """
    Determines if the report should be delayed rather than posted immediately -
    e.g. don't post a 'time to study' nudge during someone's actual sleep window.
    Currently used for logging/detection only - real delay scheduling comes
    with EventBridge during deployment.
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
    Each module is wrapped independently so one failure doesn't block the others -
    this is the error isolation pattern the whole rebuild was designed around.
    """
    status = get_module_status_summary()
    today = datetime.utcnow()
    is_monday = today.weekday() == 0

    shift = get_current_shift()
    study_status = get_today_study_status()
    print(f"[orchestrator] Starting daily run - shift: {shift}, study_status: {study_status}, Monday: {is_monday}")

    if should_delay_report(shift, study_status):
        print(f"[orchestrator] Current time falls in {shift} shift's likely sleep window - report will still post, but this is logged for future scheduling refinement.")

    # --- Video Select + Interview Set: Monday only, same topic for both ---
    if is_monday:
        try:
            video_result = run_video_select()
            status["video_select"]["ran"] = True

            # Generate this week's interview set for the SAME topic Video Select just picked,
            # so questions genuinely match each week's real, current topic, not a stale one.
            if video_result:
                try:
                    week_number, topic = get_current_week_topic()
                    run_weekly_interview_set(week_number, topic)
                    status["interview_set"]["ran"] = True
                    print(f"[orchestrator] Interview set generated for week {week_number}: {topic}")
                except Exception as interview_error:
                    status["interview_set"]["error"] = str(interview_error)
                    print(f"[orchestrator] Interview set generation failed: {interview_error}")
        except Exception as e:
            status["video_select"]["error"] = str(e)
            print(f"[orchestrator] Video Select failed: {e}")
    else:
        print("[orchestrator] Skipping Video Select and Interview Set - not Monday")

    # --- Job Scan: runs daily, but internally gates surfacing based on readiness ---
    try:
        run_job_scan()
        status["job_scan"]["ran"] = True
    except Exception as e:
        status["job_scan"]["error"] = str(e)
        print(f"[orchestrator] Job Scan failed: {e}")

    # --- Reporter: always runs last, summarizes whatever happened, even partial failures ---
    try:
        run_reporter()
        status["reporter"]["ran"] = True
    except Exception as e:
        status["reporter"]["error"] = str(e)
        print(f"[orchestrator] Reporter failed: {e}")

    print(f"[orchestrator] Daily run complete. Status: {status}")
    return status


if __name__ == "__main__":
    run_daily_orchestration()
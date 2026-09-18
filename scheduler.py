"""
scheduler.py
------------
Background daemon that periodically fetches updated forecasts, runs the
rule-based planning cycle, and dispatches notifications automatically.
"""

import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler
import planner
import notifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DEFAULT_LOCATION = "Ashta,IN"

def scheduled_job(location=DEFAULT_LOCATION):
    """Execution task for the scheduler."""
    logging.info(f"Starting automated weather & planning check for {location}...")
    try:
        summary = planner.run_planning_cycle(location)
        logging.info(f"Checked {summary['checked']} tasks. Rescheduled: {len(summary['rescheduled'])}, Unresolved: {len(summary['unresolved'])}.")
        
        # Dispatch notifications if tasks were altered
        notifier.notify_planning_summary(summary)
    except Exception as e:
        logging.error(f"Automated planning job failed: {e}")

def start_scheduler(location=DEFAULT_LOCATION, interval_hours=6):
    scheduler = BackgroundScheduler()
    
    # Run every X hours
    scheduler.add_job(
        scheduled_job,
        trigger="interval",
        hours=interval_hours,
        args=[location],
        id="weather_planner_job",
        replace_existing=True
    )
    
    # Optional: Set a fixed daily time (e.g. 07:00 AM) instead of interval:
    # scheduler.add_job(scheduled_job, 'cron', hour=7, minute=0, args=[location])

    scheduler.start()
    logging.info(f"Scheduler started. Running every {interval_hours} hours for {location}.")
    return scheduler

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run background weather scheduler.")
    parser.add_argument("--location", default=DEFAULT_LOCATION, help="Location string")
    parser.add_argument("--hours", type=int, default=6, help="Interval in hours")
    args = parser.parse_args()

    # Trigger an immediate run at launch
    scheduled_job(args.location)

    # Keep daemon process alive
    sched = start_scheduler(args.location, args.hours)
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        sched.shutdown()
        logging.info("Scheduler stopped.")
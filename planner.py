"""
planner.py
-----------
Rule-based rescheduling engine for the Weather-Aware Smart Planner.

Logic: for each pending 'outdoor' task scheduled on a day whose
rain probability exceeds RAIN_THRESHOLD, find the next day within
the 5-day forecast window whose rain probability is below the
threshold and move the task there. If no good day is found in the
window, the task is flagged (status stays 'pending' but a log entry
and a returned 'unresolved' note explain why).
"""

from datetime import datetime, timedelta

import storage
import weather_fetcher

RAIN_THRESHOLD = 0.5  # probability of precipitation (0.0 - 1.0) above which a day is "bad" for outdoor tasks


def _is_bad_weather_day(forecast):
    """A day is bad for outdoor tasks if rain probability exceeds the threshold."""
    if not forecast:
        return False  # no data -> don't block on missing info
    return forecast.get("rain_probability", 0.0) > RAIN_THRESHOLD


def run_planning_cycle(location):
    """
    Check every pending outdoor task against the forecast and
    reschedule the ones that land on a bad-weather day.

    Returns a summary dict:
    {
        'checked': int,
        'rescheduled': [ {task_id, title, old_date, new_date} ... ],
        'unresolved': [ {task_id, title, reason} ... ],
    }
    """
    forecast_days = weather_fetcher.get_5day_forecast(location)
    forecast_by_date = {f["forecast_date"]: f for f in forecast_days}

    outdoor_tasks = storage.get_tasks(status="pending", task_type="outdoor")

    result = {"checked": len(outdoor_tasks), "rescheduled": [], "unresolved": []}

    for task in outdoor_tasks:
        scheduled_date = task.get("scheduled_date")
        if not scheduled_date:
            continue  # no date set yet, nothing to check

        forecast = forecast_by_date.get(scheduled_date)
        if not _is_bad_weather_day(forecast):
            continue  # already on a good day, leave it alone

        new_date = _find_next_good_day(forecast_by_date, after_date=scheduled_date)

        if new_date:
            storage.reschedule_task(
                task["id"],
                new_date,
                reason=f"Rain probability {forecast['rain_probability']:.0%} on {scheduled_date}",
            )
            result["rescheduled"].append({
                "task_id": task["id"],
                "title": task["title"],
                "old_date": scheduled_date,
                "new_date": new_date,
            })
        else:
            result["unresolved"].append({
                "task_id": task["id"],
                "title": task["title"],
                "reason": "No good-weather day found in the 5-day forecast window",
            })

    return result


def _find_next_good_day(forecast_by_date, after_date):
    """
    Look through the forecast dates in order (after `after_date`)
    and return the first one below the rain threshold. Returns
    None if none qualify.
    """
    sorted_dates = sorted(forecast_by_date.keys())
    try:
        start_index = sorted_dates.index(after_date) + 1
    except ValueError:
        start_index = 0  # after_date not in window; scan from the start

    for date in sorted_dates[start_index:]:
        if not _is_bad_weather_day(forecast_by_date[date]):
            return date
    return None


def get_daily_plan(location, target_date=None):
    """
    Build a human-readable plan for a given date (defaults to today):
    which tasks are on, and whether the day's weather is favorable.

    Returns:
    {
        'date': str,
        'forecast': dict or None,
        'is_good_outdoor_day': bool,
        'tasks': [task dicts scheduled for that date]
    }
    """
    if target_date is None:
        target_date = datetime.now().date().isoformat()

    forecast = weather_fetcher.get_forecast_for_date(location, target_date)
    all_pending = storage.get_tasks(status="pending") + storage.get_tasks(status="rescheduled")
    tasks_today = [t for t in all_pending if t.get("scheduled_date") == target_date]

    return {
        "date": target_date,
        "forecast": forecast,
        "is_good_outdoor_day": not _is_bad_weather_day(forecast),
        "tasks": tasks_today,
    }


def find_upcoming_good_windows(location, days_ahead=5):
    """
    Return a list of upcoming dates (within the forecast window)
    that are favorable for outdoor tasks, most imminent first.
    """
    forecast_days = weather_fetcher.get_5day_forecast(location)
    good_days = [
        f["forecast_date"] for f in forecast_days
        if not _is_bad_weather_day(f)
    ]
    return sorted(good_days)


if __name__ == "__main__":
    import sys
    loc = sys.argv[1] if len(sys.argv) > 1 else "Ashta,IN"

    print(f"Running planning cycle for {loc}...")
    summary = run_planning_cycle(loc)
    print(f"Checked {summary['checked']} outdoor task(s).")
    for r in summary["rescheduled"]:
        print(f"  Rescheduled '{r['title']}': {r['old_date']} -> {r['new_date']}")
    for u in summary["unresolved"]:
        print(f"  Could not reschedule '{u['title']}': {u['reason']}")

    print("\nGood outdoor windows in the next 5 days:", find_upcoming_good_windows(loc))

"""
planner.py
Rule-based rescheduling engine for the Weather-Aware Smart Planner.
"""

from datetime import datetime, timedelta
import sys

import storage
import weather_fetcher

MAX_PRECIPITATION_THRESHOLD = 0.5  # Precip probability limit for outdoor jobs


def _check_inclement_weather(weather_data):
    # Missing data shouldn't block execution
    if not weather_data:
        return False
    
    precip_prob = weather_data.get("rain_probability", 0.0)
    return precip_prob > MAX_PRECIPITATION_THRESHOLD


def run_planning_cycle(target_loc):
    forecast_list = weather_fetcher.get_5day_forecast(target_loc) or []
    weather_map = {entry["forecast_date"]: entry for entry in forecast_list}

    outdoor_jobs = storage.get_tasks(status="pending", task_type="outdoor")
    stats = {
        "checked": len(outdoor_jobs), 
        "rescheduled": [], 
        "unresolved": []
    }

    idx = 0
    while idx < len(outdoor_jobs):
        current_job = outdoor_jobs[idx]
        idx += 1

        curr_date = current_job.get("scheduled_date")
        if not curr_date:
            continue

        day_weather = weather_map.get(curr_date)
        if not _check_inclement_weather(day_weather):
            continue

        alternative_date = _find_next_good_day(weather_map, current_date=curr_date)

        if alternative_date:
            rain_pct = day_weather.get('rain_probability', 0) * 100
            note = f"Rain probability {rain_pct:.0f}% on {curr_date}"
            
            storage.reschedule_task(
                current_job["id"],
                alternative_date,
                reason=note
            )
            
            stats["rescheduled"].append({
                "task_id": current_job["id"],
                "title": current_job["title"],
                "old_date": curr_date,
                "new_date": alternative_date,
            })
        else:
            stats["unresolved"].append({
                "task_id": current_job["id"],
                "title": current_job["title"],
                "reason": "No good-weather day found in the 5-day forecast window",
            })

    return stats


def _find_next_good_day(forecast_lookup, current_date):
    ordered_dates = sorted(list(forecast_lookup.keys()))
    
    start_pos = 0
    if current_date in ordered_dates:
        start_pos = ordered_dates.index(current_date) + 1

    remaining_dates = ordered_dates[start_pos:]
    for d in remaining_dates:
        if not _check_inclement_weather(forecast_lookup[d]):
            return d
            
    return None


def get_daily_plan(target_loc, target_date=None):
    if target_date is None:
        target_date = datetime.now().date().isoformat()

    day_forecast = weather_fetcher.get_forecast_for_date(target_loc, target_date)
    
    pending_records = storage.get_tasks(status="pending")
    rescheduled_records = storage.get_tasks(status="rescheduled")
    all_active = pending_records + rescheduled_records

    matched_tasks = []
    for record in all_active:
        if record.get("scheduled_date") == target_date:
            matched_tasks.append(record)

    is_favorable = not _check_inclement_weather(day_forecast)

    return {
        "date": target_date,
        "forecast": day_forecast,
        "is_good_outdoor_day": is_favorable,
        "tasks": matched_tasks,
    }


def find_upcoming_good_windows(target_loc, days_ahead=5):
    raw_forecast = weather_fetcher.get_5day_forecast(target_loc)
    
    favorable_dates = []
    for day in raw_forecast:
        if not _check_inclement_weather(day):
            favorable_dates.append(day["forecast_date"])

    favorable_dates.sort()
    return favorable_dates


if __name__ == "__main__":
    loc_arg = sys.argv[1] if len(sys.argv) > 1 else "Ashta,IN"

    print(f"Running planning cycle for {loc_arg}...")
    summary = run_planning_cycle(loc_arg)
    
    print(f"Checked {summary['checked']} outdoor task(s).")
    
    for item in summary["rescheduled"]:
        print(f"  Rescheduled '{item['title']}': {item['old_date']} -> {item['new_date']}")
        
    for item in summary["unresolved"]:
        print(f"  Could not reschedule '{item['title']}': {item['reason']}")

    open_windows = find_upcoming_good_windows(loc_arg)
    print("\nGood outdoor windows in the next 5 days:", open_windows)
"""
seed_demo_data.py
-------------------
One-off script to populate the database with realistic sample tasks
and cached forecasts, purely so analytics.py, the dashboard, and the
report screenshots have meaningful data to show -- without needing
a live API key or days of real usage.

Run this once:
    python seed_demo_data.py

Safe to re-run -- it just adds more sample rows each time. If you
want a clean slate first, delete data/planner.db before running.
"""

from datetime import datetime, timedelta

import storage

LOCATION = "Ashta,IN"


def seed():
    storage.init_db()

    today = datetime.now().date()
    dates = [(today + timedelta(days=i)).isoformat() for i in range(-4, 5)]

    # Realistic-looking forecast pattern: a rainy stretch in the middle
    forecast_pattern = [
        # (temp_c, condition, wind_kph, rain_probability)
        (31, "Clear", 8, 0.05),
        (30, "Clear", 10, 0.10),
        (29, "Clouds", 14, 0.30),
        (28, "Rain", 18, 0.75),
        (27, "Rain", 22, 0.85),
        (28, "Rain", 16, 0.60),
        (30, "Clear", 9, 0.15),
        (31, "Clear", 7, 0.05),
        (32, "Clear", 11, 0.10),
    ]

    for date, (temp, cond, wind, rain) in zip(dates, forecast_pattern):
        storage.save_forecast(LOCATION, date, temp, cond, wind, rain)

    # Sample tasks spread across those dates, mix of outdoor/indoor,
    # mix of completed/pending, so the charts show real variation.
    sample_tasks = [
        ("Wash car", "outdoor", "high", dates[0], True),
        ("Morning jog", "outdoor", "medium", dates[1], True),
        ("Water the garden", "outdoor", "low", dates[2], True),
        ("Cricket practice", "outdoor", "medium", dates[3], False),   # rainy day, missed
        ("Grocery run (outdoor market)", "outdoor", "medium", dates[4], False),  # rainy, missed
        ("Bike repair (in the yard)", "outdoor", "low", dates[5], True),  # rainy but done anyway
        ("Evening walk", "outdoor", "low", dates[6], True),
        ("Photography walk", "outdoor", "medium", dates[7], True),
        ("Wash windows", "outdoor", "low", dates[8], False),

        ("Read a book", "indoor", "low", dates[0], True),
        ("Study Python", "indoor", "high", dates[1], True),
        ("Organize desk", "indoor", "low", dates[2], True),
        ("Watch ML course", "indoor", "medium", dates[3], True),
        ("Clean kitchen", "indoor", "medium", dates[4], False),
        ("Practice guitar", "indoor", "low", dates[5], True),
        ("Write blog post", "indoor", "medium", dates[6], False),
    ]

    created = 0
    for title, task_type, priority, date, completed in sample_tasks:
        task_id = storage.add_task(
            title=title, task_type=task_type, priority=priority, scheduled_date=date
        )
        if completed:
            storage.complete_task(task_id)
        created += 1

    print(f"Seeded {created} sample tasks and {len(dates)} days of forecast data for {LOCATION}.")
    print("Run: python analytics.py --location \"Ashta,IN\"  to see the charts.")


if __name__ == "__main__":
    seed()

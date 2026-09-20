"""
run_interactive.py
---------------------
A simple, menu-driven way to use the Weather-Aware Smart Planner
without needing to know any command-line flags or Python syntax.

Just run:
    python run_interactive.py

...and follow the on-screen prompts. Every option here calls the
exact same underlying functions as the CLI tools and the dashboard --
this is just a friendlier front door to them.
"""

import sys

import storage
import task_manager
import weather_fetcher
import planner
import predictor
import analytics
import notifier

storage.init_db()


def pause():
    input("\nPress Enter to go back to the menu...")


def ask(prompt, default=None):
    """Ask the user for a value, showing a default if one is given."""
    suffix = f" [{default}]" if default is not None else ""
    value = input(f"{prompt}{suffix}: ").strip()
    return value if value else default


def add_task_flow():
    print("\n--- Add a New Task ---")
    title = ask("Task title (e.g. 'Wash car')")
    if not title:
        print("A title is required. Cancelled.")
        return

    print("Is this task 'outdoor' or 'indoor'?")
    task_type = ask("Type", "outdoor")
    while task_type not in ("outdoor", "indoor"):
        print("Please type exactly 'outdoor' or 'indoor'.")
        task_type = ask("Type", "outdoor")

    print("Priority: 'low', 'medium', or 'high'")
    priority = ask("Priority", "medium")
    while priority not in ("low", "medium", "high"):
        print("Please type exactly 'low', 'medium', or 'high'.")
        priority = ask("Priority", "medium")

    date = ask("Scheduled date (YYYY-MM-DD), or leave blank for none", "")
    date = date if date else None

    try:
        task_id = task_manager.create_task(
            title=title, task_type=task_type, priority=priority, scheduled_date=date
        )
        print(f"\n✅ Added task #{task_id}: '{title}'")
    except task_manager.ValidationError as e:
        print(f"\n❌ Could not add task: {e}")


def list_tasks_flow():
    print("\n--- Your Tasks ---")
    tasks = task_manager.list_tasks()
    if not tasks:
        print("You don't have any tasks yet.")
        return
    for t in tasks:
        print(task_manager.format_task_line(t))


def complete_task_flow():
    list_tasks_flow()
    task_id = ask("\nEnter the task # to mark complete")
    if not task_id or not task_id.isdigit():
        print("That doesn't look like a valid task number. Cancelled.")
        return
    try:
        task_manager.mark_complete(int(task_id))
        print(f"\n✅ Task #{task_id} marked complete.")
    except task_manager.ValidationError as e:
        print(f"\n❌ {e}")


def delete_task_flow():
    list_tasks_flow()
    task_id = ask("\nEnter the task # to delete")
    if not task_id or not task_id.isdigit():
        print("That doesn't look like a valid task number. Cancelled.")
        return
    try:
        task_manager.remove_task(int(task_id))
        print(f"\n🗑️  Task #{task_id} deleted.")
    except task_manager.ValidationError as e:
        print(f"\n❌ {e}")


def weather_flow():
    print("\n--- Check the Weather ---")
    location = ask("Enter your location (City,CountryCode)", "Ashta,IN")
    try:
        current = weather_fetcher.get_current_weather(location)
        print(f"\nRight now in {location}: {current['temperature_c']}°C, "
              f"{current['description']}, wind {current['wind_speed_kph']} km/h")

        print("\n5-day forecast:")
        for day in weather_fetcher.get_5day_forecast(location):
            print(f"  {day['forecast_date']}: {day['temperature_c']}°C, "
                  f"{day['condition']}, rain chance {day['rain_probability']:.0%}")
    except weather_fetcher.WeatherFetchError as e:
        print(f"\n❌ Couldn't fetch live weather: {e}")
        print("Tip: you can still add a forecast manually from the main menu.")


def manual_forecast_flow():
    print("\n--- Enter Weather Manually ---")
    location = ask("Location (City,CountryCode)", "Ashta,IN")
    date = ask("Date (YYYY-MM-DD)")
    temp = ask("Temperature in °C", "28")
    print(f"Condition options: {', '.join(weather_fetcher.VALID_CONDITIONS)}")
    condition = ask("Condition", "Clear")
    wind = ask("Wind speed in km/h", "10")
    rain = ask("Rain probability (0.0 to 1.0)", "0.2")

    try:
        weather_fetcher.add_manual_forecast(
            location=location, forecast_date=date, temperature_c=float(temp),
            condition=condition, wind_speed_kph=float(wind), rain_probability=float(rain),
        )
        print(f"\n✅ Saved forecast for {location} on {date}.")
    except (ValueError, TypeError) as e:
        print(f"\n❌ Could not save: {e}")


def run_planner_flow():
    print("\n--- Run the Planning Cycle ---")
    location = ask("Location (City,CountryCode)", "Ashta,IN")
    try:
        summary = planner.run_planning_cycle(location)
        notifier.notify_planning_summary(summary)
        print(f"\nChecked {summary['checked']} outdoor task(s).")
        for r in summary["rescheduled"]:
            print(f"  📅 Rescheduled '{r['title']}': {r['old_date']} -> {r['new_date']}")
        for u in summary["unresolved"]:
            print(f"  ⚠️  Could not reschedule '{u['title']}': {u['reason']}")
        if not summary["rescheduled"] and not summary["unresolved"]:
            print("  Nothing needed rescheduling.")
    except weather_fetcher.WeatherFetchError as e:
        print(f"\n❌ Weather fetch failed: {e}")


def predict_flow():
    print("\n--- Predict a Good Outdoor Day ---")
    temp = ask("Temperature in °C", "28")
    rain = ask("Rain probability (0.0 to 1.0)", "0.2")
    wind = ask("Wind speed in km/h", "10")
    from datetime import datetime
    month = datetime.now().month
    try:
        prob = predictor.predict_good_day_probability(float(temp), float(rain), float(wind), month)
        print(f"\n🔮 Predicted good-outdoor-day probability: {prob}%")
    except FileNotFoundError:
        print("\n❌ No trained model found yet. Run option to train it first.")
    except ValueError:
        print("\n❌ Please enter valid numbers.")


def train_model_flow():
    print("\n--- Train the ML Model ---")
    print("This generates sample training data and trains the predictor. Takes a few seconds...")
    df = predictor.generate_synthetic_dataset()
    metrics = predictor.train_model(df)
    print(f"\n✅ Model trained. Accuracy: {metrics['accuracy']}, ROC-AUC: {metrics['roc_auc']}")


def analytics_flow():
    print("\n--- View Analytics ---")
    location = ask("Location (City,CountryCode)", "Ashta,IN")
    report = analytics.generate_full_report(location)
    stats = report["overall_stats"]
    print(f"\nTotal tasks: {stats['total']}")
    print(f"Completed: {stats['completed']} ({stats['completion_rate_pct']}%)")
    print(f"Pending: {stats['pending']}")
    print(f"\nCharts saved to:")
    for name, path in report["charts"].items():
        print(f"  {name}: {path}")


def test_notification_flow():
    print("\n--- Test Notifications ---")
    result = notifier.notify("Test", "This is a test notification from the Smart Planner.")
    print(f"Desktop: {'sent' if result['desktop'] else 'not available'}")
    print(f"Email: {'sent' if result['email'] else 'not configured or failed'}")


MENU = """
==================================================
  WEATHER-AWARE SMART PLANNER — Easy Mode
==================================================
  1. Add a task
  2. View all tasks
  3. Mark a task complete
  4. Delete a task
  5. Check the weather (live)
  6. Enter weather manually
  7. Run the planning cycle (auto-reschedule)
  8. Predict a good outdoor day (ML)
  9. Train the ML model
 10. View analytics / charts
 11. Test notifications
 12. Exit
==================================================
"""

ACTIONS = {
    "1": add_task_flow,
    "2": list_tasks_flow,
    "3": complete_task_flow,
    "4": delete_task_flow,
    "5": weather_flow,
    "6": manual_forecast_flow,
    "7": run_planner_flow,
    "8": predict_flow,
    "9": train_model_flow,
    "10": analytics_flow,
    "11": test_notification_flow,
}


def main():
    print("Welcome! This tool will guide you step by step — just type the number of what you want to do.")
    while True:
        print(MENU)
        choice = input("Enter your choice (1-12): ").strip()

        if choice == "12":
            print("\nGoodbye!")
            sys.exit(0)

        action = ACTIONS.get(choice)
        if action is None:
            print("\n❌ Please enter a number between 1 and 12.")
            continue

        action()
        pause()


if __name__ == "__main__":
    main()

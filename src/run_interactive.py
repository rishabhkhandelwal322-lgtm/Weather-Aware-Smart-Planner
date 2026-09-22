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

try:
    import termcharts
    HAS_TERMCHARTS = True
except ImportError:
    HAS_TERMCHARTS = False

try:
    import plotext as plotext_plt
    HAS_PLOTEXT = True
except ImportError:
    HAS_PLOTEXT = False

try:
    from rich.console import Console
    from rich.table import Table as RichTable
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

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
        print(f"\nAdded task #{task_id}: '{title}'")
    except task_manager.ValidationError as e:
        print(f"\nCould not add task: {e}")


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
        print(f"\nTask #{task_id} marked complete.")
    except task_manager.ValidationError as e:
        print(f"\n{e}")


def delete_task_flow():
    list_tasks_flow()
    task_id = ask("\nEnter the task # to delete")
    if not task_id or not task_id.isdigit():
        print("That doesn't look like a valid task number. Cancelled.")
        return
    try:
        task_manager.remove_task(int(task_id))
        print(f"\nDeleted task #{task_id}.")
    except task_manager.ValidationError as e:
        print(f"\n{e}")


def show_temperature_terminal_chart(dates, temps):
    """Render a real line chart of temperature over the forecast window, in-terminal."""
    if not HAS_PLOTEXT:
        return
    try:
        x = list(range(len(dates)))
        plotext_plt.clf()
        plotext_plt.plot(x, temps, marker="dot", color="orange")
        plotext_plt.xticks(x, dates)
        plotext_plt.title("Temperature Trend (°C)")
        plotext_plt.plotsize(70, 16)
        plotext_plt.show()
    except Exception:
        pass  # never let a display glitch interrupt the app


def show_precipitation_terminal_chart(dates, rain_pct):
    """Render a real bar chart of rain probability over the forecast window, in-terminal."""
    if not HAS_PLOTEXT:
        return
    try:
        plotext_plt.clf()
        plotext_plt.bar(dates, rain_pct, color="blue")
        plotext_plt.title("Precipitation Trend (% chance of rain)")
        plotext_plt.plotsize(70, 16)
        plotext_plt.show()
    except Exception:
        pass


def weather_flow():
    print("\n--- Check the Weather ---")
    location = ask("Enter your location (City,CountryCode)", "Ashta,IN")
    try:
        current = weather_fetcher.get_current_weather(location)
        print(f"\nRight now in {location}: {current['temperature_c']}°C, "
              f"{current['description']}, wind {current['wind_speed_kph']} km/h")

        forecast_days = weather_fetcher.get_5day_forecast(location)
        print("\n5-day forecast:")
        for day in forecast_days:
            print(f"  {day['forecast_date']}: {day['temperature_c']}°C, "
                  f"{day['condition']}, rain chance {day['rain_probability']:.0%}")

        if HAS_PLOTEXT and forecast_days:
            dates = [d["forecast_date"] for d in forecast_days]
            temps = [d["temperature_c"] for d in forecast_days]
            rain_pct = [round(d["rain_probability"] * 100, 1) for d in forecast_days]
            print()
            show_temperature_terminal_chart(dates, temps)
            print()
            show_precipitation_terminal_chart(dates, rain_pct)
        elif not HAS_PLOTEXT:
            print("\n(Tip: pip install plotext  for in-terminal temperature/precipitation graphs.)")

    except weather_fetcher.WeatherFetchError as e:
        print(f"\nCouldn't fetch live weather: {e}")
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
        print(f"\nSaved forecast for {location} on {date}.")
    except (ValueError, TypeError) as e:
        print(f"\nCould not save: {e}")


def run_planner_flow():
    print("\n--- Run the Planning Cycle ---")
    location = ask("Location (City,CountryCode)", "Ashta,IN")
    try:
        summary = planner.run_planning_cycle(location)
        notifier.notify_planning_summary(summary)
        print(f"\nChecked {summary['checked']} outdoor task(s).")
        for r in summary["rescheduled"]:
            print(f"  Rescheduled '{r['title']}': {r['old_date']} -> {r['new_date']}")
        for u in summary["unresolved"]:
            print(f"  Could not reschedule '{u['title']}': {u['reason']}")
        if not summary["rescheduled"] and not summary["unresolved"]:
            print("  Nothing needed rescheduling.")
    except weather_fetcher.WeatherFetchError as e:
        print(f"\nWeather fetch failed: {e}")


def predict_flow():
    print("\n--- Predict a Good Outdoor Day ---")
    temp = ask("Temperature in °C", "28")
    rain = ask("Rain probability (0.0 to 1.0)", "0.2")
    wind = ask("Wind speed in km/h", "10")
    from datetime import datetime
    month = datetime.now().month
    try:
        prob = predictor.predict_good_day_probability(float(temp), float(rain), float(wind), month)
        print(f"\nPredicted good-outdoor-day probability: {prob}%")
    except FileNotFoundError:
        print("\nNo trained model found yet. Run option to train it first.")
    except ValueError:
        print("\nPlease enter valid numbers.")


def train_model_flow():
    print("\n--- Train the ML Model ---")
    print("This generates sample training data and trains the predictor. Takes a few seconds...")
    df = predictor.generate_synthetic_dataset()
    metrics = predictor.train_model(df)
    print(f"\nModel trained. Accuracy: {metrics['accuracy']}, ROC-AUC: {metrics['roc_auc']}")


def ascii_bar(label, value, max_value, width=30, unit="%"):
    """Render a single labeled horizontal bar using block characters."""
    if max_value <= 0:
        filled = 0
    else:
        filled = int((value / max_value) * width)
    bar = "█" * filled + "░" * (width - filled)
    value_str = f"{value:>5.1f}{unit}" if unit else f"{int(value):>5d}"
    return f"  {label:<12} {bar} {value_str}"


def print_bar_chart(title, data, unit="%", max_value=100):
    """Print a titled group of ASCII bars. data is a list of (label, value)."""
    print(f"\n{title}")
    print("  " + "-" * (len(title)))
    for label, value in data:
        print(ascii_bar(label, value, max_value, unit=unit))


def show_charts_popup(chart_paths):
    """
    Open the generated chart PNGs in a real popup window using
    matplotlib's interactive backend. Falls back gracefully with a
    message if no display/GUI backend is available (e.g. over SSH).
    """
    try:
        import matplotlib
        matplotlib.use("TkAgg", force=True)
        import matplotlib.pyplot as plt

        names = list(chart_paths.keys())
        fig, axes = plt.subplots(1, len(names), figsize=(6 * len(names), 5))
        if len(names) == 1:
            axes = [axes]

        for ax, name in zip(axes, names):
            img = plt.imread(chart_paths[name])
            ax.imshow(img)
            ax.axis("off")
            ax.set_title(name.replace("_", " ").title())

        fig.suptitle("Weather-Aware Smart Planner — Analytics", fontsize=14, weight="bold")
        fig.tight_layout()
        plt.show()
        return True
    except Exception as e:
        print(f"\nCouldn't open a popup window ({e}).")
        print("You can still open the chart PNG files directly from the reports folder.")
        return False


def safe_term_bar(data, title, fallback_pairs):
    """
    Try to render a termcharts bar; if the data is degenerate (all
    zero/equal, which triggers a known termcharts division-by-zero
    bug) or anything else goes wrong, fall back to the plain ASCII
    bar chart instead of crashing the whole program.
    """
    values = list(data.values())
    if not values or len(set(values)) <= 1:
        # All values identical (including all-zero) -- termcharts can't
        # handle this, so go straight to the safe ASCII fallback.
        print_bar_chart(title, fallback_pairs)
        return
    try:
        print("\n" + termcharts.bar(data, title=title, mode="v"))
    except Exception:
        print_bar_chart(title, fallback_pairs)


def safe_term_pie(data, title):
    values = list(data.values())
    if not values or len(set(values)) <= 1:
        print(f"\n{title}")
        for k, v in data.items():
            print(f"  {k}: {v}")
        return
    try:
        print(termcharts.pie(data, title=title))
    except Exception:
        print(f"\n{title}")
        for k, v in data.items():
            print(f"  {k}: {v}")


def analytics_flow():
    print("\n--- View Analytics ---")
    location = ask("Location (City,CountryCode)", "Ashta,IN")
    report = analytics.generate_full_report(location)
    stats = report["overall_stats"]
    by_type = report["by_type"]
    weather = report["weather_correlation"]

    print(f"\nTotal tasks: {stats['total']}")
    print(f"Completed: {stats['completed']} ({stats['completion_rate_pct']}%)")
    print(f"Pending: {stats['pending']}")

    if HAS_TERMCHARTS:
        safe_term_bar(
            {"Outdoor": by_type["outdoor"]["rate_pct"], "Indoor": by_type["indoor"]["rate_pct"]},
            "Completion Rate: Outdoor vs Indoor (%)",
            [("Outdoor", by_type["outdoor"]["rate_pct"]), ("Indoor", by_type["indoor"]["rate_pct"])],
        )
        safe_term_bar(
            {"Clear Day": weather["clear_day"]["rate_pct"], "Rainy Day": weather["rainy_day"]["rate_pct"]},
            "Outdoor Completion vs Weather (%)",
            [("Clear Day", weather["clear_day"]["rate_pct"]), ("Rainy Day", weather["rainy_day"]["rate_pct"])],
        )

        status_counts = {
            "Completed": stats["completed"], "Pending": stats["pending"],
            "Rescheduled": stats["rescheduled"], "Cancelled": stats["cancelled"],
        }
        status_counts = {k: v for k, v in status_counts.items() if v > 0}
        if status_counts:
            safe_term_pie(status_counts, "Overall Task Status")
        else:
            print("(No completed/pending/rescheduled/cancelled tasks yet to chart.)")
    else:
        print_bar_chart(
            "Task Completion Rate: Outdoor vs Indoor",
            [("Outdoor", by_type["outdoor"]["rate_pct"]), ("Indoor", by_type["indoor"]["rate_pct"])],
        )
        print_bar_chart(
            "Outdoor Completion vs Weather",
            [("Clear Day", weather["clear_day"]["rate_pct"]), ("Rainy Day", weather["rainy_day"]["rate_pct"])],
        )
        status_counts = {
            "Completed": stats["completed"], "Pending": stats["pending"],
            "Rescheduled": stats["rescheduled"], "Cancelled": stats["cancelled"],
        }
        max_count = max(status_counts.values()) if status_counts.values() else 1
        print_bar_chart(
            "Overall Task Status (counts)",
            list(status_counts.items()), unit="", max_value=max(max_count, 1),
        )
        print("\n(Tip: pip install termcharts rich  for full color pie/bar charts.)")

    print(f"\nImage versions of these charts were also saved to:")
    for name, path in report["charts"].items():
        print(f"  {name}: {path}")

    show = ask("\nOpen these charts in a popup window now? (y/n)", "y")
    if show.lower().startswith("y"):
        show_charts_popup(report["charts"])


def test_notification_flow():
    print("\n--- Test Notifications ---")
    result = notifier.notify("Test", "This is a test notification from the Smart Planner.")
    print(f"Desktop: {'sent' if result['desktop'] else 'not available'}")
    print(f"Email: {'sent' if result['email'] else 'not configured or failed'}")


def _correlation_cell_color(value):
    """Map a correlation value (-1 to 1) to a rich color name."""
    if value >= 0.6:
        return "bold red"
    if value >= 0.2:
        return "red"
    if value > -0.2:
        return "white"
    if value > -0.6:
        return "blue"
    return "bold blue"


def correlation_heatmap_flow():
    print("\n--- Weather Correlation Heatmap ---")
    print("Correlation between weather variables and the 'good outdoor day' label,")
    print("computed from the same data the ML model was trained on.\n")

    corr = analytics.get_weather_correlation_matrix()

    if HAS_RICH:
        console = Console()
        table = RichTable(title="Weather Variable Correlation Heatmap")
        table.add_column("")
        for col in corr.columns:
            table.add_column(col, justify="center")

        for row_name in corr.index:
            cells = [row_name]
            for col_name in corr.columns:
                value = corr.loc[row_name, col_name]
                color = _correlation_cell_color(value)
                cells.append(f"[{color}]{value:.2f}[/{color}]")
            table.add_row(*cells)

        console.print(table)
    else:
        # plain-text fallback, no colors
        cols = list(corr.columns)
        header = "".ljust(16) + "".join(c[:10].rjust(11) for c in cols)
        print(header)
        for row_name in corr.index:
            row_str = row_name[:15].ljust(16)
            for col_name in cols:
                row_str += f"{corr.loc[row_name, col_name]:.2f}".rjust(11)
            print(row_str)
        print("\n(Tip: pip install rich  for a colored heatmap.)")


def desktop_gui_flow():
    print("\n--- Opening Desktop Window ---")
    print("A window should appear on your screen. Close it when you're done to return here.")
    try:
        import desktop_gui
        desktop_gui.launch()
    except ImportError as e:
        print(f"\nCouldn't open the desktop window: {e}")
        print("Tip: tkinter usually ships with Python by default on Windows; "
              "if it's missing, reinstall Python from python.org with 'tcl/tk and IDLE' checked.")
    except Exception as e:
        print(f"\nThe desktop window closed unexpectedly: {e}")


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
 12. Weather correlation heatmap
 13. Open desktop window (GUI)
 14. Exit
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
    "12": correlation_heatmap_flow,
    "13": desktop_gui_flow,
}


def main():
    print("Welcome! This tool will guide you step by step — just type the number of what you want to do.")
    while True:
        print(MENU)
        choice = input("Enter your choice (1-14): ").strip()

        if choice == "14":

            print("\nGoodbye!")
            sys.exit(0)

        action = ACTIONS.get(choice)
        if action is None:
            print("\nPlease enter a number between 1 and 14.")
            continue

        action()
        pause()


if __name__ == "__main__":
    main()

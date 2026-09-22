"""
analytics.py
-------------
Generates productivity analytics by correlating task completion data
(from the tasks table) with cached weather forecasts (from the
forecasts table), and produces chart images summarizing the trends.

Charts are saved as PNG files under reports/, so they can be dropped
straight into the project report as screenshots/results.

Usage:
    python analytics.py --location "Ashta,IN"
"""

from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")  # non-interactive backend, safe for headless/script use
import matplotlib.pyplot as plt

import storage

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def get_completion_stats():
    """
    Overall task stats: counts by status and the completion rate.
    Returns a dict.
    """
    all_tasks = storage.get_tasks()
    total = len(all_tasks)
    counts = defaultdict(int)
    for task in all_tasks:
        counts[task["status"]] += 1

    completed = counts.get("completed", 0)
    completion_rate = round(completed / total * 100, 1) if total else 0.0

    return {
        "total": total,
        "completed": completed,
        "pending": counts.get("pending", 0),
        "rescheduled": counts.get("rescheduled", 0),
        "cancelled": counts.get("cancelled", 0),
        "completion_rate_pct": completion_rate,
    }


def get_completion_by_task_type():
    """
    Completion rate broken down by outdoor vs indoor tasks.
    Returns {task_type: {'total': n, 'completed': n, 'rate_pct': x}}
    """
    all_tasks = storage.get_tasks()
    breakdown = {
        "outdoor": {"total": 0, "completed": 0},
        "indoor": {"total": 0, "completed": 0},
    }

    for task in all_tasks:
        t = task["task_type"]
        breakdown[t]["total"] += 1
        if task["status"] == "completed":
            breakdown[t]["completed"] += 1

    for t, stats in breakdown.items():
        stats["rate_pct"] = round(
            stats["completed"] / stats["total"] * 100, 1
        ) if stats["total"] else 0.0

    return breakdown


def get_weather_completion_correlation(location):
    """
    Join outdoor tasks against the cached forecast for their
    scheduled_date, and bucket completion outcomes by whether that
    day was rainy (rain_probability > 0.5) or not.

    Returns {'rainy_day': {'total': n, 'completed': n, 'rate_pct': x},
             'clear_day':  {'total': n, 'completed': n, 'rate_pct': x}}
    """
    outdoor_tasks = [
        t for t in storage.get_tasks(task_type="outdoor")
        if t.get("scheduled_date")
    ]

    buckets = {
        "rainy_day": {"total": 0, "completed": 0},
        "clear_day": {"total": 0, "completed": 0},
    }

    for task in outdoor_tasks:
        forecast = storage.get_forecast(location, task["scheduled_date"])
        if not forecast:
            continue  # no weather data for that date, skip from correlation

        bucket = "rainy_day" if forecast["rain_probability"] > 0.5 else "clear_day"
        buckets[bucket]["total"] += 1
        if task["status"] == "completed":
            buckets[bucket]["completed"] += 1

    for bucket, stats in buckets.items():
        stats["rate_pct"] = round(
            stats["completed"] / stats["total"] * 100, 1
        ) if stats["total"] else 0.0

    return buckets


def get_reschedule_log(limit=50):
    """Return the most recent 'rescheduled' log entries, for a timeline chart."""
    logs = storage.get_logs(limit=limit)
    return [log for log in logs if log["action"] == "rescheduled"]


# ------------------------------------------------------------- charts ----

def plot_completion_by_type(save_path=None):
    """Bar chart: completion rate for outdoor vs indoor tasks."""
    breakdown = get_completion_by_task_type()
    types = list(breakdown.keys())
    rates = [breakdown[t]["rate_pct"] for t in types]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(types, rates, color=["#4C9F70", "#4C7BF4"])
    ax.set_ylabel("Completion Rate (%)")
    ax.set_title("Task Completion Rate: Outdoor vs Indoor")
    ax.set_ylim(0, 110)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 2, f"{rate}%", ha="center")

    save_path = save_path or REPORTS_DIR / "completion_by_type.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def plot_weather_correlation(location, save_path=None):
    """Bar chart: outdoor task completion rate on rainy vs clear days."""
    buckets = get_weather_completion_correlation(location)
    labels = ["Clear Day", "Rainy Day"]
    rates = [buckets["clear_day"]["rate_pct"], buckets["rainy_day"]["rate_pct"]]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, rates, color=["#F5A623", "#4A6FA5"])
    ax.set_ylabel("Completion Rate (%)")
    ax.set_title(f"Outdoor Task Completion vs Weather ({location})")
    ax.set_ylim(0, 110)
    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 2, f"{rate}%", ha="center")

    save_path = save_path or REPORTS_DIR / "weather_correlation.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def plot_status_breakdown(save_path=None):
    """Pie chart: overall task status breakdown."""
    stats = get_completion_stats()
    labels = ["Completed", "Pending", "Rescheduled", "Cancelled"]
    values = [stats["completed"], stats["pending"], stats["rescheduled"], stats["cancelled"]]

    # Drop zero-value slices so the pie chart doesn't render empty wedges
    filtered = [(l, v) for l, v in zip(labels, values) if v > 0]
    if not filtered:
        return None
    labels, values = zip(*filtered)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90)
    ax.set_title("Overall Task Status Breakdown")

    save_path = save_path or REPORTS_DIR / "status_breakdown.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def generate_full_report(location):
    """
    Generate all analytics charts and return a summary dict with
    the stats and the paths to each generated chart image. A chart
    path is None if there wasn't enough data to plot it (e.g. no
    tasks yet) -- callers must check for None before using a path.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    completion_chart = plot_completion_by_type()
    weather_chart = plot_weather_correlation(location)
    status_chart = plot_status_breakdown()

    return {
        "overall_stats": get_completion_stats(),
        "by_type": get_completion_by_task_type(),
        "weather_correlation": get_weather_completion_correlation(location),
        "charts": {
            "completion_by_type": str(completion_chart) if completion_chart else None,
            "weather_correlation": str(weather_chart) if weather_chart else None,
            "status_breakdown": str(status_chart) if status_chart else None,
        },
    }


# --------------------------------------------------- weather trend charts ----

def get_temperature_series(location):
    """
    Return the 5-day forecast as parallel lists of dates and temperatures,
    for plotting a temperature trend line.
    """
    import weather_fetcher
    forecast_days = weather_fetcher.get_5day_forecast(location)
    dates = [f["forecast_date"] for f in forecast_days]
    temps = [f["temperature_c"] for f in forecast_days]
    return dates, temps


def get_precipitation_series(location):
    """
    Return the 5-day forecast as parallel lists of dates and rain
    probabilities (0-100%), for plotting a precipitation trend.
    """
    import weather_fetcher
    forecast_days = weather_fetcher.get_5day_forecast(location)
    dates = [f["forecast_date"] for f in forecast_days]
    rain_pct = [f["rain_probability"] * 100 for f in forecast_days]
    return dates, rain_pct


def plot_temperature_trend(location, save_path=None):
    """Line chart: forecasted temperature (°C) over the next 5 days."""
    dates, temps = get_temperature_series(location)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(dates, temps, marker="o", color="#E67E22", linewidth=2)
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"5-Day Temperature Trend — {location}")
    ax.grid(True, alpha=0.3)
    for x, y in zip(dates, temps):
        ax.annotate(f"{y}°", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

    save_path = save_path or REPORTS_DIR / "temperature_trend.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


def plot_precipitation_trend(location, save_path=None):
    """Bar chart: forecasted rain probability (%) over the next 5 days."""
    dates, rain_pct = get_precipitation_series(location)

    fig, ax = plt.subplots(figsize=(7, 4))
    colors_list = ["#4A6FA5" if r <= 50 else "#2C5F8A" for r in rain_pct]
    bars = ax.bar(dates, rain_pct, color=colors_list)
    ax.set_ylabel("Rain Probability (%)")
    ax.set_title(f"5-Day Precipitation Trend — {location}")
    ax.set_ylim(0, 110)
    for bar, val in zip(bars, rain_pct):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2, f"{val:.0f}%", ha="center", fontsize=8)

    save_path = save_path or REPORTS_DIR / "precipitation_trend.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


# ------------------------------------------------- correlation heatmap ----

def get_weather_correlation_matrix():
    """
    Compute the correlation matrix between weather variables and the
    good-outdoor-day label, using the same synthetic training dataset
    the ML predictor was trained on. Returns a pandas DataFrame.
    Generates the dataset first if it doesn't exist yet.
    """
    import pandas as pd
    import predictor

    if not predictor.DATA_PATH.exists():
        predictor.generate_synthetic_dataset()

    df = pd.read_csv(predictor.DATA_PATH)
    columns = ["temperature_c", "rain_probability", "wind_speed_kph", "month", "is_good_day"]
    return df[columns].corr()


def plot_correlation_heatmap(save_path=None):
    """
    Save a matplotlib heatmap image of the weather-variable correlation
    matrix (temperature, rain probability, wind speed, month, and the
    good-outdoor-day label used to train the ML model).
    """
    corr = get_weather_correlation_matrix()

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(corr.columns, fontsize=8)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            value = corr.values[i, j]
            text_color = "white" if abs(value) > 0.6 else "black"
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=text_color, fontsize=8)

    ax.set_title("Weather Variable Correlation Heatmap\n(ML training data)", fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Correlation")

    save_path = save_path or REPORTS_DIR / "correlation_heatmap.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)
    return save_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate weather-vs-productivity analytics.")
    parser.add_argument("--location", default="Ashta,IN", help="Location to correlate weather against")
    args = parser.parse_args()

    print(f"Generating analytics report for {args.location}...")
    report = generate_full_report(args.location)

    print("\nOverall stats:", report["overall_stats"])
    print("By task type:", report["by_type"])
    print("Weather correlation:", report["weather_correlation"])
    print("\nCharts saved to:")
    for name, path in report["charts"].items():
        print(f"  {name}: {path}")

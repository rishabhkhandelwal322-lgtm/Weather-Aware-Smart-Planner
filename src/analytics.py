"""
analytics.py
Script to match task progress against local weather forecasts.
Generates PNG plots in the reports/ folder for documentation.

Quick run:
    python analytics.py --location "Ashta,IN"
"""

from pathlib import Path
from collections import defaultdict
import matplotlib

# Set non-interactive backend before importing pyplot
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import storage

# Output folder for generated plots
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def get_completion_stats():
    # Grab every task from the database
    tasks = storage.get_tasks()
    n_tasks = len(tasks)
    
    tally = defaultdict(int)
    for t in tasks:
        tally[t.get("status", "unknown")] += 1

    done_count = tally.get("completed", 0)
    pct = round((done_count / n_tasks) * 100, 1) if n_tasks > 0 else 0.0

    return {
        "total": n_tasks,
        "completed": done_count,
        "pending": tally.get("pending", 0),
        "rescheduled": tally.get("rescheduled", 0),
        "cancelled": tally.get("cancelled", 0),
        "completion_rate_pct": pct,
    }


def get_completion_by_task_type():
    # Split metrics across outdoor and indoor categories
    tasks = storage.get_tasks()
    summary = {
        "outdoor": {"total": 0, "completed": 0},
        "indoor": {"total": 0, "completed": 0},
    }

    for task in tasks:
        category = task.get("task_type")
        if category in summary:
            summary[category]["total"] += 1
            if task.get("status") == "completed":
                summary[category]["completed"] += 1

    for cat_name, info in summary.items():
        tot = info["total"]
        info["rate_pct"] = round((info["completed"] / tot) * 100, 1) if tot else 0.0

    return summary


def get_weather_completion_correlation(location):
    # Filter outdoor tasks that actually have a schedule attached
    outdoor_list = [
        item for item in storage.get_tasks(task_type="outdoor")
        if item.get("scheduled_date")
    ]

    weather_buckets = {
        "rainy_day": {"total": 0, "completed": 0},
        "clear_day": {"total": 0, "completed": 0},
    }

    for item in outdoor_list:
        forecast_data = storage.get_forecast(location, item["scheduled_date"])
        if not forecast_data:
            continue  # No cached forecast available for this date

        is_rainy = forecast_data.get("rain_probability", 0) > 0.5
        group_key = "rainy_day" if is_rainy else "clear_day"

        weather_buckets[group_key]["total"] += 1
        if item.get("status") == "completed":
            weather_buckets[group_key]["completed"] += 1

    for key, data in weather_buckets.items():
        total_items = data["total"]
        data["rate_pct"] = round((data["completed"] / total_items) * 100, 1) if total_items else 0.0

    return weather_buckets


def get_reschedule_log(limit=50):
    entries = storage.get_logs(limit=limit)
    return [entry for entry in entries if entry.get("action") == "rescheduled"]


# --- Chart Builders ---

def plot_completion_by_type(save_path=None):
    data = get_completion_by_task_type()
    categories = list(data.keys())
    percentages = [data[c]["rate_pct"] for c in categories]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar([c.capitalize() for c in categories], percentages, color=["#4C9F70", "#4C7BF4"])
    
    ax.set_ylabel("Completion Rate (%)")
    ax.set_title("Task Completion Rate: Outdoor vs Indoor")
    ax.set_ylim(0, 110)

    for bar, pct in zip(bars, percentages):
        ax.text(bar.get_x() + bar.get_width() / 2, pct + 2, f"{pct}%", ha="center")

    out_file = save_path or REPORTS_DIR / "completion_by_type.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file


def plot_weather_correlation(location, save_path=None):
    groups = get_weather_completion_correlation(location)
    labels = ["Clear Day", "Rainy Day"]
    rates = [groups["clear_day"]["rate_pct"], groups["rainy_day"]["rate_pct"]]

    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(labels, rates, color=["#F5A623", "#4A6FA5"])
    
    ax.set_ylabel("Completion Rate (%)")
    ax.set_title(f"Outdoor Task Completion vs Weather ({location})")
    ax.set_ylim(0, 110)

    for bar, rate in zip(bars, rates):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 2, f"{rate}%", ha="center")

    out_file = save_path or REPORTS_DIR / "weather_correlation.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file


def plot_status_breakdown(save_path=None):
    stats = get_completion_stats()
    categories = ["Completed", "Pending", "Rescheduled", "Cancelled"]
    counts = [stats["completed"], stats["pending"], stats["rescheduled"], stats["cancelled"]]

    # Omit statuses that sit at 0 tasks
    active = [(cat, count) for cat, count in zip(categories, counts) if count > 0]
    if not active:
        return None

    plot_labels, plot_values = zip(*active)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(plot_values, labels=plot_labels, autopct="%1.0f%%", startangle=90)
    ax.set_title("Overall Task Status Breakdown")

    out_file = save_path or REPORTS_DIR / "status_breakdown.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file


def generate_full_report(location):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    chart_type = plot_completion_by_type()
    chart_weather = plot_weather_correlation(location)
    chart_status = plot_status_breakdown()

    return {
        "overall_stats": get_completion_stats(),
        "by_type": get_completion_by_task_type(),
        "weather_correlation": get_weather_completion_correlation(location),
        "charts": {
            "completion_by_type": str(chart_type) if chart_type else None,
            "weather_correlation": str(chart_weather) if chart_weather else None,
            "status_breakdown": str(chart_status) if chart_status else None,
        },
    }


# --- Weather Trend Visuals ---

def get_temperature_series(location):
    import weather_fetcher
    days = weather_fetcher.get_5day_forecast(location)
    return [d["forecast_date"] for d in days], [d["temperature_c"] for d in days]


def get_precipitation_series(location):
    import weather_fetcher
    days = weather_fetcher.get_5day_forecast(location)
    return [d["forecast_date"] for d in days], [d["rain_probability"] * 100 for d in days]


def plot_temperature_trend(location, save_path=None):
    dates, temps = get_temperature_series(location)

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(dates, temps, marker="o", color="#E67E22", linewidth=2)
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"5-Day Temperature Trend — {location}")
    ax.grid(True, alpha=0.3)

    for x_val, y_val in zip(dates, temps):
        ax.annotate(f"{y_val}°", (x_val, y_val), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)

    out_file = save_path or REPORTS_DIR / "temperature_trend.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file


def plot_precipitation_trend(location, save_path=None):
    dates, rain_pct = get_precipitation_series(location)

    fig, ax = plt.subplots(figsize=(7, 4))
    bar_colors = ["#4A6FA5" if p <= 50 else "#2C5F8A" for p in rain_pct]
    bars = ax.bar(dates, rain_pct, color=bar_colors)
    
    ax.set_ylabel("Rain Probability (%)")
    ax.set_title(f"5-Day Precipitation Trend — {location}")
    ax.set_ylim(0, 110)

    for bar, val in zip(bars, rain_pct):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 2, f"{val:.0f}%", ha="center", fontsize=8)

    out_file = save_path or REPORTS_DIR / "precipitation_trend.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file


# --- Correlation Heatmap ---

def get_weather_correlation_matrix():
    import pandas as pd
    import predictor

    if not predictor.DATA_PATH.exists():
        predictor.generate_synthetic_dataset()

    df = pd.read_csv(predictor.DATA_PATH)
    target_cols = ["temperature_c", "rain_probability", "wind_speed_kph", "month", "is_good_day"]
    return df[target_cols].corr()


def plot_correlation_heatmap(save_path=None):
    corr = get_weather_correlation_matrix()

    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)

    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(corr.columns, fontsize=8)

    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            v = corr.values[i, j]
            clr = "white" if abs(v) > 0.6 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", color=clr, fontsize=8)

    ax.set_title("Weather Variable Correlation Heatmap\n(ML training data)", fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8, label="Correlation")

    out_file = save_path or REPORTS_DIR / "correlation_heatmap.png"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    return out_file


if __name__ == "__main__":
    import argparse

    cli = argparse.ArgumentParser(description="Generate weather-vs-productivity analytics.")
    cli.add_argument("--location", default="Ashta,IN", help="Location to correlate weather against")
    parsed = cli.parse_args()

    print(f"Generating analytics report for {parsed.location}...")
    output_report = generate_full_report(parsed.location)

    print("\nOverall stats:", output_report["overall_stats"])
    print("By task type:", output_report["by_type"])
    print("Weather correlation:", output_report["weather_correlation"])
    print("\nCharts saved to:")
    for key_name, file_path in output_report["charts"].items():
        print(f"  {key_name}: {file_path}")
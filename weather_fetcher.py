"""
weather_fetcher.py
-------------------
Fetches current weather and a 5-day forecast from the OpenWeatherMap
free-tier API (Current Weather Data + 5 Day / 3 Hour Forecast).

The 3-hour forecast blocks are aggregated into one summary per day
(worst-case rain probability, max wind, avg temp) so the rest of the
app can reason about "days" rather than 3-hour slices.

Results are cached in the local database via storage.py, so repeated
calls for the same location/date within a day don't re-hit the API.
"""

import os
from datetime import datetime, timedelta
from collections import defaultdict

import requests
from dotenv import load_dotenv

import storage

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherFetchError(Exception):
    """Raised when the weather API can't be reached or returns an error."""


def _check_api_key():
    if not API_KEY:
        raise WeatherFetchError(
            "OPENWEATHER_API_KEY is not set. Add it to a .env file in the project root."
        )


def get_current_weather(location):
    """
    Fetch current conditions for a location (city name, e.g. 'Ashta,IN').
    Returns a dict with temperature_c, condition, wind_speed_kph, humidity.
    Raises WeatherFetchError on failure (network issue, bad location, etc).
    """
    _check_api_key()
    params = {"q": location, "appid": API_KEY, "units": "metric"}

    try:
        response = requests.get(CURRENT_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise WeatherFetchError(f"Could not fetch current weather: {exc}") from exc

    data = response.json()
    return {
        "location": location,
        "temperature_c": data["main"]["temp"],
        "condition": data["weather"][0]["main"],
        "description": data["weather"][0]["description"],
        "wind_speed_kph": data["wind"]["speed"] * 3.6,  # m/s -> km/h
        "humidity": data["main"]["humidity"],
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
    }


def get_5day_forecast(location, use_cache=True):
    """
    Fetch and aggregate the 5-day/3-hour forecast into one summary
    per calendar day. Returns a list of dicts, one per day:
    {date, avg_temp_c, condition, max_wind_kph, rain_probability}

    If use_cache is True, checks storage for each date first and
    only calls the API for dates not already cached (or if none
    are cached at all for this location).
    """
    today = datetime.now().date()
    dates_needed = [(today + timedelta(days=i)).isoformat() for i in range(5)]

    if use_cache:
        cached = [storage.get_forecast(location, d) for d in dates_needed]
        if all(cached):
            return cached

    _check_api_key()
    params = {"q": location, "appid": API_KEY, "units": "metric"}

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        raise WeatherFetchError(f"Could not fetch forecast: {exc}") from exc

    data = response.json()
    by_day = defaultdict(list)

    for entry in data["list"]:
        day = entry["dt_txt"].split(" ")[0]  # 'YYYY-MM-DD'
        by_day[day].append(entry)

    daily_summaries = []
    for day, entries in sorted(by_day.items()):
        temps = [e["main"]["temp"] for e in entries]
        winds = [e["wind"]["speed"] * 3.6 for e in entries]
        rain_probs = [e.get("pop", 0.0) for e in entries]  # 'pop' = probability of precip
        conditions = [e["weather"][0]["main"] for e in entries]

        # Most frequent condition of the day, as the representative label
        condition = max(set(conditions), key=conditions.count)

        summary = {
            "location": location,
            "forecast_date": day,
            "temperature_c": round(sum(temps) / len(temps), 1),
            "condition": condition,
            "wind_speed_kph": round(max(winds), 1),
            "rain_probability": round(max(rain_probs), 2),
        }
        daily_summaries.append(summary)

        storage.save_forecast(
            location=location,
            forecast_date=day,
            temperature_c=summary["temperature_c"],
            condition=summary["condition"],
            wind_speed_kph=summary["wind_speed_kph"],
            rain_probability=summary["rain_probability"],
        )

    return daily_summaries


def get_forecast_for_date(location, target_date, use_cache=True):
    """
    Convenience lookup: return the forecast summary for one specific
    date (ISO string 'YYYY-MM-DD'), pulling the full 5-day set if needed.
    Returns None if the date is outside the available forecast window.
    """
    if use_cache:
        cached = storage.get_forecast(location, target_date)
        if cached:
            return cached

    summaries = get_5day_forecast(location, use_cache=False)
    for summary in summaries:
        if summary["forecast_date"] == target_date:
            return summary
    return None


if __name__ == "__main__":
    import sys
    loc = sys.argv[1] if len(sys.argv) > 1 else "Ashta,IN"
    try:
        print("Current:", get_current_weather(loc))
        print("\n5-day forecast:")
        for day in get_5day_forecast(loc):
            print(" ", day)
    except WeatherFetchError as e:
        print(f"Error: {e}")

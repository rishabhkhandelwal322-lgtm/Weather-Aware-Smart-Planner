"""
test_planner.py
------------------
Unit tests for planner.py's rescheduling logic. The weather API is
never called directly in tests — forecast data is seeded straight
into storage via storage.save_forecast(), so tests are fast, fully
offline, and deterministic.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import storage
import planner

LOCATION = "TestCity,IN"


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test_planner.db")
    storage.init_db()
    yield


def seed_forecast(date, rain_probability, temp=28, wind=10, condition="Clear"):
    storage.save_forecast(LOCATION, date, temp, condition, wind, rain_probability)


def test_is_bad_weather_day_above_threshold():
    forecast = {"rain_probability": 0.7}
    assert planner._is_bad_weather_day(forecast) is True


def test_is_bad_weather_day_below_threshold():
    forecast = {"rain_probability": 0.3}
    assert planner._is_bad_weather_day(forecast) is False


def test_is_bad_weather_day_missing_forecast_defaults_to_good():
    assert planner._is_bad_weather_day(None) is False


def test_find_next_good_day_skips_bad_days():
    forecast_by_date = {
        "2026-09-18": {"rain_probability": 0.8},
        "2026-09-19": {"rain_probability": 0.6},
        "2026-09-20": {"rain_probability": 0.2},
    }
    result = planner._find_next_good_day(forecast_by_date, after_date="2026-09-18")
    assert result == "2026-09-20"


def test_find_next_good_day_returns_none_if_all_bad():
    forecast_by_date = {
        "2026-09-18": {"rain_probability": 0.8},
        "2026-09-19": {"rain_probability": 0.9},
    }
    result = planner._find_next_good_day(forecast_by_date, after_date="2026-09-18")
    assert result is None


def test_run_planning_cycle_reschedules_rainy_task(monkeypatch):
    seed_forecast("2026-09-18", rain_probability=0.8)
    seed_forecast("2026-09-19", rain_probability=0.1)

    # bypass the live API entirely: return the cached forecasts as-is
    monkeypatch.setattr(
        "weather_fetcher.get_5day_forecast",
        lambda location, use_cache=True: [
            storage.get_forecast(LOCATION, "2026-09-18"),
            storage.get_forecast(LOCATION, "2026-09-19"),
        ],
    )

    task_id = storage.add_task("Wash car", "outdoor", scheduled_date="2026-09-18")
    summary = planner.run_planning_cycle(LOCATION)

    assert summary["checked"] == 1
    assert len(summary["rescheduled"]) == 1
    assert summary["rescheduled"][0]["new_date"] == "2026-09-19"

    task = storage.get_task(task_id)
    assert task["status"] == "rescheduled"
    assert task["scheduled_date"] == "2026-09-19"


def test_run_planning_cycle_leaves_good_day_task_alone(monkeypatch):
    seed_forecast("2026-09-18", rain_probability=0.1)

    monkeypatch.setattr(
        "weather_fetcher.get_5day_forecast",
        lambda location, use_cache=True: [storage.get_forecast(LOCATION, "2026-09-18")],
    )

    task_id = storage.add_task("Jog", "outdoor", scheduled_date="2026-09-18")
    summary = planner.run_planning_cycle(LOCATION)

    assert summary["rescheduled"] == []
    assert summary["unresolved"] == []
    task = storage.get_task(task_id)
    assert task["status"] == "pending"
    assert task["scheduled_date"] == "2026-09-18"


def test_run_planning_cycle_marks_unresolved_when_no_good_day(monkeypatch):
    seed_forecast("2026-09-18", rain_probability=0.9)
    seed_forecast("2026-09-19", rain_probability=0.85)

    monkeypatch.setattr(
        "weather_fetcher.get_5day_forecast",
        lambda location, use_cache=True: [
            storage.get_forecast(LOCATION, "2026-09-18"),
            storage.get_forecast(LOCATION, "2026-09-19"),
        ],
    )

    storage.add_task("Picnic", "outdoor", scheduled_date="2026-09-18")
    summary = planner.run_planning_cycle(LOCATION)

    assert summary["rescheduled"] == []
    assert len(summary["unresolved"]) == 1
    assert summary["unresolved"][0]["title"] == "Picnic"


def test_run_planning_cycle_ignores_indoor_tasks(monkeypatch):
    seed_forecast("2026-09-18", rain_probability=0.9)
    monkeypatch.setattr(
        "weather_fetcher.get_5day_forecast",
        lambda location, use_cache=True: [storage.get_forecast(LOCATION, "2026-09-18")],
    )

    storage.add_task("Read book", "indoor", scheduled_date="2026-09-18")
    summary = planner.run_planning_cycle(LOCATION)

    assert summary["checked"] == 0
    assert summary["rescheduled"] == []

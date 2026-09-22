"""
test_predictor.py
--------------------
Unit tests for predictor.py's synthetic data generation, model
training, and prediction behavior. Uses a small dataset and a
temporary model path so tests run quickly and never touch the
real trained model shipped with the project.

If pandas (a dependency of predictor.py) can't be imported on this
machine -- e.g. blocked by a local security policy such as Windows
Smart App Control -- this whole file is skipped with a clear reason
instead of crashing the entire test run. On any machine where pandas
imports normally, these tests run exactly as written.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

predictor = pytest.importorskip(
    "predictor",
    reason="predictor.py (and its pandas dependency) could not be imported on this machine",
)


@pytest.fixture(autouse=True)
def temp_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(predictor, "DATA_DIR", tmp_path)
    monkeypatch.setattr(predictor, "DATA_PATH", tmp_path / "historical_weather.csv")
    monkeypatch.setattr(predictor, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(predictor, "MODEL_PATH", tmp_path / "weather_model.pkl")
    yield


def test_generate_synthetic_dataset_shape_and_columns():
    df = predictor.generate_synthetic_dataset(n_samples=200, seed=1)
    assert len(df) == 200
    expected_cols = {"temperature_c", "rain_probability", "wind_speed_kph", "month", "is_good_day"}
    assert expected_cols.issubset(set(df.columns))


def test_generate_synthetic_dataset_value_ranges():
    df = predictor.generate_synthetic_dataset(n_samples=300, seed=2)
    assert df["rain_probability"].between(0, 1).all()
    assert df["month"].between(1, 12).all()
    assert df["is_good_day"].isin([0, 1]).all()
    assert (df["wind_speed_kph"] >= 0).all()


def test_generate_synthetic_dataset_is_reproducible_with_same_seed():
    df1 = predictor.generate_synthetic_dataset(n_samples=100, seed=42)
    df2 = predictor.generate_synthetic_dataset(n_samples=100, seed=42)
    assert df1.equals(df2)


def test_train_model_returns_reasonable_metrics():
    df = predictor.generate_synthetic_dataset(n_samples=800, seed=42)
    metrics = predictor.train_model(df)
    assert 0.5 <= metrics["accuracy"] <= 1.0
    assert 0.5 <= metrics["roc_auc"] <= 1.0
    assert metrics["n_train"] + metrics["n_test"] == 800
    assert predictor.MODEL_PATH.exists()


def test_predict_good_day_probability_without_trained_model_raises():
    with pytest.raises(FileNotFoundError):
        predictor.predict_good_day_probability(25, 0.1, 10, 6)


def test_predict_clear_day_scores_higher_than_rainy_day():
    df = predictor.generate_synthetic_dataset(n_samples=1000, seed=42)
    predictor.train_model(df)

    clear_day_score = predictor.predict_good_day_probability(
        temperature_c=25, rain_probability=0.05, wind_speed_kph=8, month=4
    )
    rainy_day_score = predictor.predict_good_day_probability(
        temperature_c=28, rain_probability=0.85, wind_speed_kph=20, month=7
    )

    assert 0 <= clear_day_score <= 100
    assert 0 <= rainy_day_score <= 100
    assert clear_day_score > rainy_day_score


def test_predict_for_forecast_uses_forecast_dict_fields():
    df = predictor.generate_synthetic_dataset(n_samples=600, seed=42)
    predictor.train_model(df)

    forecast = {
        "forecast_date": "2026-09-20",
        "temperature_c": 26,
        "rain_probability": 0.1,
        "wind_speed_kph": 9,
    }
    score = predictor.predict_for_forecast(forecast)
    assert 0 <= score <= 100

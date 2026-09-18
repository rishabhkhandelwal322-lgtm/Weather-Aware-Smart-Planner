"""
predictor.py
-------------
Machine-learning layer that estimates the PROBABILITY (0-100%) that
a given day is a good day for outdoor tasks, going a step beyond the
rule-based threshold in planner.py.

Since real multi-year historical weather logs aren't available for
this coursework project, this module generates a synthetic but
realistic training dataset (data/historical_weather.csv) using
seasonally-varying weather patterns with random noise, then trains
a RandomForestClassifier on it. The "ground truth" label for training
is produced by a slightly fuzzy version of the planner's own rules,
so the model learns a smoothed, probabilistic version of that logic
rather than just memorizing a hard cutoff.

Usage:
    python predictor.py --train                # generate data + train + save model
    python predictor.py --predict 30 0.4 15     # temp_c, rain_prob, wind_kph
"""

import random
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

DATA_DIR = Path(__file__).parent / "data"
MODEL_DIR = Path(__file__).parent / "models"
DATA_PATH = DATA_DIR / "historical_weather.csv"
MODEL_PATH = MODEL_DIR / "weather_model.pkl"

FEATURE_COLUMNS = ["temperature_c", "rain_probability", "wind_speed_kph", "month"]


def generate_synthetic_dataset(n_samples=2000, seed=42):
    """
    Generate a synthetic historical weather dataset with realistic
    seasonal variation, and a fuzzy 'good outdoor day' label used as
    the training target.

    Columns: temperature_c, rain_probability, wind_speed_kph, month, is_good_day
    """
    rng = np.random.default_rng(seed)
    random.seed(seed)

    rows = []
    for _ in range(n_samples):
        month = rng.integers(1, 13)

        # Rough seasonal temperature curve (Northern-hemisphere-style, adjustable)
        seasonal_base = 22 + 10 * np.sin((month - 3) / 12 * 2 * np.pi)
        temperature_c = rng.normal(loc=seasonal_base, scale=5)

        # Monsoon-ish months (Jun-Sep) get higher rain probability on average
        if month in (6, 7, 8, 9):
            rain_probability = np.clip(rng.beta(2, 2), 0, 1)
        else:
            rain_probability = np.clip(rng.beta(1.5, 5), 0, 1)

        wind_speed_kph = np.clip(rng.normal(loc=12, scale=6), 0, 60)

        # Fuzzy ground-truth label: mostly rule-based, with some noise
        # so the classifier learns soft boundaries instead of a hard cutoff.
        base_good = (
            rain_probability < 0.4
            and 10 <= temperature_c <= 36
            and wind_speed_kph < 30
        )
        flip = rng.random() < 0.07  # 7% label noise to avoid an unrealistically perfect signal
        is_good_day = int(base_good != flip)

        rows.append({
            "temperature_c": round(temperature_c, 1),
            "rain_probability": round(rain_probability, 2),
            "wind_speed_kph": round(wind_speed_kph, 1),
            "month": month,
            "is_good_day": is_good_day,
        })

    df = pd.DataFrame(rows)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    return df


def train_model(df=None):
    """
    Train a RandomForestClassifier on the (synthetic) historical
    dataset and save it to MODEL_PATH. Returns evaluation metrics.
    """
    if df is None:
        df = pd.read_csv(DATA_PATH) if DATA_PATH.exists() else generate_synthetic_dataset()

    X = df[FEATURE_COLUMNS]
    y = df["is_good_day"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=150, max_depth=6, random_state=42, class_weight="balanced"
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 3),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 3),
        "n_train": len(X_train),
        "n_test": len(X_test),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return metrics


def _load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No trained model found at {MODEL_PATH}. Run `python predictor.py --train` first."
        )
    return joblib.load(MODEL_PATH)


def predict_good_day_probability(temperature_c, rain_probability, wind_speed_kph, month):
    """
    Return the model's estimated probability (0-100, float) that a day
    with the given conditions is a good outdoor day.
    """
    model = _load_model()
    features = pd.DataFrame([{
        "temperature_c": temperature_c,
        "rain_probability": rain_probability,
        "wind_speed_kph": wind_speed_kph,
        "month": month,
    }])
    proba = model.predict_proba(features)[0][1]
    return round(proba * 100, 1)


def predict_for_forecast(forecast):
    """
    Convenience wrapper: takes a forecast dict as returned by
    weather_fetcher.get_5day_forecast()/get_forecast_for_date()
    (keys: temperature_c, rain_probability, wind_speed_kph, forecast_date)
    and returns the predicted good-outdoor-day probability.
    """
    from datetime import datetime

    month = datetime.strptime(forecast["forecast_date"], "%Y-%m-%d").month
    return predict_good_day_probability(
        temperature_c=forecast["temperature_c"],
        rain_probability=forecast["rain_probability"],
        wind_speed_kph=forecast["wind_speed_kph"],
        month=month,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train or query the outdoor-day predictor.")
    parser.add_argument("--train", action="store_true", help="Generate data and train the model")
    parser.add_argument(
        "--predict", nargs=3, metavar=("TEMP_C", "RAIN_PROB", "WIND_KPH"), type=float,
        help="Predict probability for given conditions (uses current month)",
    )
    args = parser.parse_args()

    if args.train:
        print("Generating synthetic historical dataset...")
        df = generate_synthetic_dataset()
        print(f"  {len(df)} rows written to {DATA_PATH}")
        print("Training model...")
        metrics = train_model(df)
        print(f"  Done. Test accuracy={metrics['accuracy']}, ROC-AUC={metrics['roc_auc']}")
        print(f"  Model saved to {MODEL_PATH}")

    elif args.predict:
        from datetime import datetime
        temp, rain, wind = args.predict
        month = datetime.now().month
        prob = predict_good_day_probability(temp, rain, wind, month)
        print(f"Predicted good-outdoor-day probability: {prob}%")

    else:
        parser.print_help()

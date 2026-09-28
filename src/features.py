from __future__ import annotations

import numpy as np
import pandas as pd


MODEL_FEATURES = [
    "hour",
    "season_code",
    "year_index",
    "month",
    "holiday",
    "weekday",
    "workingday",
    "weather_code",
    "temp_c",
    "feels_like_c",
    "humidity_pct",
    "windspeed_scaled",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "trend_days",
]


def add_model_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add leakage-safe calendar and cyclical features."""
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data["hour_sin"] = np.sin(2 * np.pi * data["hour"] / 24)
    data["hour_cos"] = np.cos(2 * np.pi * data["hour"] / 24)
    data["month_sin"] = np.sin(2 * np.pi * data["month"] / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["month"] / 12)
    origin = data["timestamp"].min().normalize()
    data["trend_days"] = (data["timestamp"] - origin).dt.total_seconds() / 86_400
    return data


def chronological_split(frame: pd.DataFrame, holdout_fraction: float = 0.20) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between 0 and 1")
    ordered = frame.sort_values("timestamp").reset_index(drop=True)
    split_index = int(len(ordered) * (1 - holdout_fraction))
    if split_index <= 0 or split_index >= len(ordered):
        raise ValueError("split produced an empty training or holdout set")
    return ordered.iloc[:split_index].copy(), ordered.iloc[split_index:].copy()


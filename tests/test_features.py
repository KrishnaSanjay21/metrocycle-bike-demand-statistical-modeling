import numpy as np
import pandas as pd

from src.features import MODEL_FEATURES, add_model_features, chronological_split


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2012-01-01", periods=10, freq="h"),
            "hour": list(range(10)),
            "month": [1] * 10,
        }
    )


def test_cyclical_features_are_bounded():
    result = add_model_features(sample_frame())
    for column in ("hour_sin", "hour_cos", "month_sin", "month_cos"):
        assert result[column].between(-1, 1).all()


def test_chronological_split_preserves_time_order():
    result = add_model_features(sample_frame())
    train, test = chronological_split(result, 0.2)
    assert len(train) == 8
    assert len(test) == 2
    assert train["timestamp"].max() < test["timestamp"].min()


def test_model_features_exclude_target_leakage():
    assert "rental_count" not in MODEL_FEATURES
    assert "casual_rentals" not in MODEL_FEATURES
    assert "registered_rentals" not in MODEL_FEATURES


def test_midnight_hour_cycle_is_expected():
    result = add_model_features(sample_frame())
    assert np.isclose(result.loc[0, "hour_sin"], 0.0)
    assert np.isclose(result.loc[0, "hour_cos"], 1.0)


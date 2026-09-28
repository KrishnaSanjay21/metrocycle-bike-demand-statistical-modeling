import numpy as np

from src.modeling import evaluate_predictions


def test_perfect_predictions_have_zero_error():
    actual = np.array([0, 3, 10, 25])
    metrics = evaluate_predictions(actual, actual)
    assert metrics["mae"] == 0
    assert metrics["rmse"] == 0
    assert metrics["rmsle"] == 0
    assert metrics["r2"] == 1


def test_negative_predictions_are_clipped():
    metrics = evaluate_predictions(np.array([0, 1]), np.array([-5, 1]))
    assert metrics["mae"] == 0


import sqlite3

import pandas as pd

from src.config import DATABASE, METRICS_CSV


def test_database_quality_checks_pass():
    with sqlite3.connect(DATABASE) as connection:
        failed = connection.execute(
            "SELECT COUNT(*) FROM dq_results WHERE severity = 'Critical' AND status != 'PASS'"
        ).fetchone()[0]
    assert failed == 0


def test_rental_counts_reconcile():
    with sqlite3.connect(DATABASE) as connection:
        failures = connection.execute(
            "SELECT COUNT(*) FROM mart_hourly_demand WHERE rental_count != casual_rentals + registered_rentals"
        ).fetchone()[0]
    assert failures == 0


def test_holdout_starts_after_training_period():
    metrics = pd.read_csv(METRICS_CSV)
    train_end = pd.to_datetime(metrics["train_end"])
    holdout_start = pd.to_datetime(metrics["holdout_start"])
    assert (train_end < holdout_start).all()


def test_model_metrics_are_finite():
    metrics = pd.read_csv(METRICS_CSV)
    assert metrics[["mae", "rmse", "rmsle", "r2"]].notna().all().all()
    assert (metrics[["mae", "rmse", "rmsle"]] >= 0).all().all()

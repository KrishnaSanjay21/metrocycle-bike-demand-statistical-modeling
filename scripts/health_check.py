from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.config import DATABASE, HOURLY_CSV, METRICS_CSV, MODEL_BUNDLE, PROVENANCE_JSON


def collect_status() -> dict[str, object]:
    required = {
        "source_csv": HOURLY_CSV,
        "source_provenance": PROVENANCE_JSON,
        "analytical_database": DATABASE,
        "model_metrics": METRICS_CSV,
        "forecast_bundle": MODEL_BUNDLE,
    }
    status: dict[str, object] = {
        "ready": all(path.exists() for path in required.values()),
        "artifacts": {name: path.exists() for name, path in required.items()},
    }
    if DATABASE.exists():
        with sqlite3.connect(DATABASE) as connection:
            status["analytical_rows"] = connection.execute("SELECT COUNT(*) FROM mart_hourly_demand").fetchone()[0]
            status["critical_quality_failures"] = connection.execute(
                "SELECT COUNT(*) FROM dq_results WHERE severity = 'Critical' AND status != 'PASS'"
            ).fetchone()[0]
    if METRICS_CSV.exists():
        metrics = pd.read_csv(METRICS_CSV).sort_values("rmse")
        status["best_model"] = metrics.iloc[0]["model"]
        status["best_holdout_rmse"] = round(float(metrics.iloc[0]["rmse"]), 3)
    status["ready"] = bool(status["ready"] and status.get("critical_quality_failures", 1) == 0)
    return status


if __name__ == "__main__":
    result = collect_status()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["ready"] else 1)

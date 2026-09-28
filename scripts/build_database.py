from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from scripts.download_data import download
from src.config import DATABASE, HOURLY_CSV, SQL_DIR, ensure_directories


EXPECTED_COLUMNS = [
    "instant",
    "dteday",
    "season",
    "yr",
    "mnth",
    "hr",
    "holiday",
    "weekday",
    "workingday",
    "weathersit",
    "temp",
    "atemp",
    "hum",
    "windspeed",
    "casual",
    "registered",
    "cnt",
]


def build_database() -> None:
    ensure_directories()
    if not HOURLY_CSV.exists():
        download()

    source = pd.read_csv(HOURLY_CSV)
    missing = sorted(set(EXPECTED_COLUMNS) - set(source.columns))
    if missing:
        raise ValueError(f"Published source is missing required columns: {missing}")
    source = source[EXPECTED_COLUMNS]

    with sqlite3.connect(DATABASE) as connection:
        connection.executescript((SQL_DIR / "01_schema.sql").read_text(encoding="utf-8"))
        source.to_sql("raw_hourly_bike", connection, if_exists="append", index=False)
        connection.executescript((SQL_DIR / "02_transform.sql").read_text(encoding="utf-8"))
        connection.executescript((SQL_DIR / "03_quality_checks.sql").read_text(encoding="utf-8"))
        failed = connection.execute(
            "SELECT COUNT(*) FROM dq_results WHERE severity = 'Critical' AND status != 'PASS'"
        ).fetchone()[0]
        if failed:
            raise RuntimeError(f"Database build stopped: {failed} critical data-quality checks failed")


if __name__ == "__main__":
    build_database()

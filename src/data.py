from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DATABASE


def read_hourly(database: Path = DATABASE) -> pd.DataFrame:
    with sqlite3.connect(database) as connection:
        frame = pd.read_sql_query(
            "SELECT * FROM mart_hourly_demand ORDER BY timestamp",
            connection,
            parse_dates=["service_date", "timestamp"],
        )
    return frame


def read_quality_results(database: Path = DATABASE) -> pd.DataFrame:
    with sqlite3.connect(database) as connection:
        return pd.read_sql_query("SELECT * FROM dq_results ORDER BY severity, check_name", connection)


def read_daily_summary(database: Path = DATABASE) -> pd.DataFrame:
    with sqlite3.connect(database) as connection:
        return pd.read_sql_query(
            "SELECT * FROM mart_daily_summary ORDER BY service_date",
            connection,
            parse_dates=["service_date"],
        )


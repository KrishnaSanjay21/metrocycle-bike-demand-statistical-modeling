from __future__ import annotations

from threading import Lock

from scripts.build_database import build_database
from scripts.download_data import download
from src.config import DATABASE, HOURLY_CSV, METRICS_CSV, MODEL_BUNDLE
from src.modeling import train_models

_BOOTSTRAP_LOCK = Lock()


def ensure_project_ready() -> None:
    """Create the analytical database and model artifacts when absent."""
    with _BOOTSTRAP_LOCK:
        if not HOURLY_CSV.exists():
            download()
        if not DATABASE.exists():
            build_database()
        if not METRICS_CSV.exists() or not MODEL_BUNDLE.exists():
            train_models()


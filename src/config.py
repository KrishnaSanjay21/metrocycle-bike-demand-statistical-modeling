from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
OUTPUT_DIR = ROOT / "outputs"
SQL_DIR = ROOT / "sql"

UCI_DATASET_PAGE = "https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset"
UCI_DOWNLOAD_URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
DATASET_DOI = "https://doi.org/10.24432/C5W894"

ZIP_PATH = RAW_DIR / "bike-sharing-dataset.zip"
HOURLY_CSV = RAW_DIR / "hour.csv"
DAILY_CSV = RAW_DIR / "day.csv"
SOURCE_README = RAW_DIR / "Readme.txt"
PROVENANCE_JSON = RAW_DIR / "provenance.json"
DATABASE = PROCESSED_DIR / "metrocycle.db"

METRICS_CSV = OUTPUT_DIR / "model_metrics.csv"
PREDICTIONS_CSV = OUTPUT_DIR / "holdout_predictions.csv"
COEFFICIENTS_CSV = OUTPUT_DIR / "coefficient_effects.csv"
HYPOTHESES_CSV = OUTPUT_DIR / "hypothesis_tests.csv"
DIAGNOSTICS_CSV = OUTPUT_DIR / "model_diagnostics.csv"
BOOTSTRAP_CSV = OUTPUT_DIR / "bootstrap_metrics.csv"
MODEL_BUNDLE = OUTPUT_DIR / "forecast_models.joblib"

HOLDOUT_FRACTION = 0.20
RANDOM_SEED = 42


def ensure_directories() -> None:
    for directory in (RAW_DIR, PROCESSED_DIR, OUTPUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)


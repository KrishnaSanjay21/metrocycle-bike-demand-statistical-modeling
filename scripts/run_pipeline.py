from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_database import build_database
from scripts.download_data import download
from src.modeling import train_models


def main() -> None:
    print("[1/3] Downloading the published UCI Bike Sharing dataset...")
    download()
    print("[2/3] Building the SQLite analytical layer and running quality checks...")
    build_database()
    print("[3/3] Training models, diagnostics, and uncertainty estimates...")
    artifacts = train_models()
    best = artifacts.metrics.iloc[0]
    print(f"Pipeline complete. Best holdout RMSE: {best['model']} ({best['rmse']:.2f}).")


if __name__ == "__main__":
    main()


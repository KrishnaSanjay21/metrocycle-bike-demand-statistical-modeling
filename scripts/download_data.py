from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from src.config import (
    DAILY_CSV,
    DATASET_DOI,
    HOURLY_CSV,
    PROVENANCE_JSON,
    RAW_DIR,
    SOURCE_README,
    UCI_DATASET_PAGE,
    UCI_DOWNLOAD_URL,
    ZIP_PATH,
    ensure_directories,
)


def sha256(path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(force: bool = False) -> None:
    ensure_directories()
    if HOURLY_CSV.exists() and DAILY_CSV.exists() and not force:
        return

    response = requests.get(UCI_DOWNLOAD_URL, timeout=90)
    response.raise_for_status()
    ZIP_PATH.write_bytes(response.content)

    with zipfile.ZipFile(ZIP_PATH) as archive:
        members = {name.lower(): name for name in archive.namelist()}
        for target_name, destination in (
            ("hour.csv", HOURLY_CSV),
            ("day.csv", DAILY_CSV),
            ("readme.txt", SOURCE_README),
        ):
            match = next((actual for lowered, actual in members.items() if lowered.endswith(target_name)), None)
            if match is None:
                raise FileNotFoundError(f"{target_name} was not found in the UCI archive")
            destination.write_bytes(archive.read(match))

    provenance = {
        "dataset": "Bike Sharing",
        "publisher": "UCI Machine Learning Repository",
        "dataset_page": UCI_DATASET_PAGE,
        "download_url": UCI_DOWNLOAD_URL,
        "doi": DATASET_DOI,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive_sha256": sha256(ZIP_PATH),
        "hour_csv_sha256": sha256(HOURLY_CSV),
        "day_csv_sha256": sha256(DAILY_CSV),
    }
    PROVENANCE_JSON.write_text(json.dumps(provenance, indent=2), encoding="utf-8")


if __name__ == "__main__":
    download()

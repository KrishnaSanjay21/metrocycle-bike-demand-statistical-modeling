from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_pipeline import main as run_pipeline


def run() -> None:
    """Rebuild and validate the entire project from source."""
    run_pipeline()
    subprocess.run([sys.executable, "-m", "pytest"], cwd=ROOT, check=True)

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60).run()
    if app.exception:
        raise RuntimeError(f"Executive dashboard failed: {app.exception}")
    for page in ["Statistical Inference", "Model Diagnostics", "Scenario Explorer", "Data Quality"]:
        app.sidebar.radio[0].set_value(page).run()
        if app.exception:
            raise RuntimeError(f"{page} failed: {app.exception}")
    print("End-to-end validation passed for the pipeline, tests, and all dashboard views.")


if __name__ == "__main__":
    run()

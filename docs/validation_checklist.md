# Validation Checklist

Run `python scripts/ci_validate.py` to rebuild and validate the project from source in one command. The script is portable to GitHub Actions or another CI runner without relying on local artifacts.

- [x] Download the official UCI archive over HTTPS
- [x] Record SHA-256 source hashes
- [x] Build the SQLite raw and analytical layers
- [x] Fail on critical SQL data-quality exceptions
- [x] Fit inferential and predictive models
- [x] Generate chronological holdout metrics
- [x] Generate bootstrap confidence intervals
- [x] Run unit and integration tests
- [x] Render every Streamlit dashboard view without exceptions

Generated data and model artifacts are excluded from version control. This ensures CI validates the reproducible pipeline rather than relying on locally generated files.

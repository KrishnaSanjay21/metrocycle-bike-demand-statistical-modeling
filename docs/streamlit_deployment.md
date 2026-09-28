# Streamlit Deployment Guide

## Community Cloud settings

- Repository: `KrishnaSanjay21/metrocycle-bike-demand-statistical-modeling`
- Branch: `main`
- Main file: `streamlit_app.py`
- Python: 3.12

No secrets are required. The app uses an open UCI HTTPS endpoint.

## First launch

Generated data and model artifacts are excluded from Git. On its first launch, `src/bootstrap.py`:

1. Downloads the official UCI archive.
2. Creates the SQLite analytical database.
3. Executes critical data-quality checks.
4. Fits the statistical and predictive models.
5. Writes dashboard metrics and bootstrap intervals.

The first launch can take about one minute. Later runs reuse cached artifacts until the app is rebooted or redeployed.

## Pre-deployment checks

```bash
python scripts/run_pipeline.py
python scripts/health_check.py
pytest
streamlit run streamlit_app.py
```

`health_check.py` returns a nonzero exit code when required artifacts are missing or a critical data-quality rule fails.

## Accuracy of deployment claims

Community Cloud deployment demonstrates a public portfolio application. It should not be described as a production forecasting service: there is no live feed, service-level agreement, model monitoring backend, or automated retraining schedule.


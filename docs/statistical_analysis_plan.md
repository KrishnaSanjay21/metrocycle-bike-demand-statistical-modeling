# Statistical Analysis Plan

## 1. Objective

Estimate adjusted associations between hourly bike-rental counts and calendar/weather conditions, quantify uncertainty, and compare operational prediction models on a future chronological holdout.

## 2. Data source

The analysis uses the hourly file from the UCI Bike Sharing dataset (Capital Bikeshare, 2011–2012). The source contains hourly counts, calendar attributes, normalized weather measures, and casual/registered component counts. The pipeline records download time and SHA-256 hashes.

## 3. Analysis population and unit

- Unit: one observed system-hour.
- Inclusion: every row in `hour.csv` with valid date, hour, and rental count.
- Exclusion: rows that fail critical data-quality rules.
- Target: `cnt`, renamed `rental_count`.
- Leakage controls: `casual` and `registered` are excluded from predictors because they sum exactly to the target.

## 4. Variables

Primary exposure groups are hour, season, weather category, holiday status, working-day status, temperature, humidity, and wind speed. Temperature is represented by linear and squared terms. Year and elapsed days adjust for system growth and secular trend.

Month and weekday are retained for predictive models but excluded from the inferential GLM because they are structurally related to season and working-day indicators. This avoids rank-deficient inference.

## 5. Models

### Inferential models

1. Poisson GLM with log link.
2. Negative Binomial GLM with log link and method-of-moments NB2 alpha estimated from Poisson residuals.
3. HC1 heteroskedasticity-robust standard errors.

The Poisson dispersion ratio is a specification diagnostic. A ratio materially above one supports the Negative Binomial variance function.

### Predictive comparators

- Hour/working-day grouped-mean baseline
- Log-linear Ridge regression
- Regularized Poisson regression
- Negative Binomial GLM
- Histogram Gradient Boosting regressor

## 6. Validation

Observations are sorted by timestamp. The first 80% form the training sample and the final 20% form the holdout. Random splitting is prohibited because neighboring hours are temporally dependent and a random split would leak future operating regimes into training.

Primary predictive metric: RMSE. Secondary metrics: MAE, RMSLE, and R². Nonparametric 95% intervals use 500 row-level bootstrap resamples of the holdout. Because time dependence remains, these intervals are descriptive and may be narrower than block-bootstrap intervals.

## 7. Hypotheses

Joint Wald tests evaluate:

1. Hour-of-day coefficients are jointly zero.
2. Linear and quadratic temperature terms are jointly zero.
3. Holiday coefficient equals zero.
4. Working-day coefficient equals zero.
5. Adverse-weather coefficients are jointly zero.

Nominal alpha is 0.05. Holm adjustment controls family-wise error across the five pre-specified tests. Effect estimates are reported with robust 95% confidence intervals regardless of statistical significance.

## 8. Diagnostics

- Poisson Pearson dispersion ratio
- NB2 alpha and AIC
- Variance inflation factors for continuous predictors
- Lag-1 autocorrelation of deviance residuals
- Chronological actual-versus-predicted plots
- Bootstrap uncertainty for holdout metrics

Residual autocorrelation is treated as evidence that standard GLMs do not fully model the temporal process. No causal interpretation is permitted.

## 9. Missing data

The published source reports no missing values. Critical SQL checks verify required fields. Predictive pipelines include median imputation defensively; the inferential analysis uses complete analytical rows.

## 10. Reproducibility

The random seed is 42. Package ranges are pinned in `requirements.txt`. The full workflow runs through `python scripts/run_pipeline.py`; tests run with `pytest`.


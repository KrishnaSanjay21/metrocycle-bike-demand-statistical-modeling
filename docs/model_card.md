# Model Card

## Intended use

Portfolio demonstration of statistical count modeling, uncertainty quantification, diagnostics, and chronological model validation. The scenario explorer supports educational operational planning exercises.

## Not intended for

- Current Capital Bikeshare staffing or fleet allocation
- Causal claims about weather or calendar policies
- Safety-critical or real-time dispatch decisions
- Generalization to other cities without re-estimation and validation

## Models

The Negative Binomial GLM is the primary inference model. Gradient Boosting is the strongest holdout predictor. These roles are deliberately separated: predictive superiority does not make a model better for coefficient-based inference.

## Performance

On the final 20% chronological holdout, Gradient Boosting achieves RMSE 67.99 and R² 0.905. The Negative Binomial GLM achieves RMSE 122.45 and R² 0.692. The grouped-mean baseline achieves RMSE 144.92.

## Uncertainty

GLM coefficients use HC1 robust 95% confidence intervals. Hypothesis tests use Holm-adjusted p-values. Holdout metric intervals use 500 bootstrap resamples. The bootstrap currently resamples rows rather than time blocks and does not fully preserve serial dependence.

## Known limitations

- Data are from 2011–2012 and one metropolitan system.
- The dataset contains system counts, not trip-level origins or destinations.
- Weather and calendar variables may proxy for omitted behaviors and events.
- Residual lag-1 autocorrelation is approximately 0.75.
- Tree predictions do not extrapolate reliably beyond the observed feature range.
- Heavy-weather observations are rare; corresponding estimates are imprecise.

## Monitoring recommendations

If adapted to live operations, monitor feature drift, missingness, residual calibration, RMSE by hour/weather, and retraining performance using rolling-origin validation. Replace row bootstrap with block bootstrap and add lagged-demand features only when real-time availability is assured.


# Executive Recommendation

## Decision

Use the Gradient Boosting model as the operational forecasting benchmark, but retain the Negative Binomial GLM as the explanation layer. The two models answer different questions: one minimizes future-period error; the other quantifies adjusted associations and uncertainty.

## Evidence

The Gradient Boosting model reduces chronological holdout RMSE from 144.92 for the hour/working-day baseline to 67.99, a 53% reduction. It explains approximately 90.5% of holdout variance. The Negative Binomial model is less accurate but reveals interpretable demand patterns after controlling for time, season, weather, and system growth.

The Poisson dispersion ratio of 28.9 confirms that a basic Poisson variance assumption is inappropriate. In the Negative Binomial specification, light rain or snow corresponds to roughly 40% lower expected demand than clear weather, holidays to roughly 19% lower demand, and the fitted temperature response peaks near 26.8°C. These are adjusted associations, not causal impacts.

## Operational actions

1. Build staffing and rebalancing plans around hour-specific profiles rather than daily averages.
2. Use adverse-weather scenarios to stress-test capacity and labor plans.
3. Prefer the Gradient Boosting forecast for near-term planning while using the GLM to explain broad demand drivers.
4. Track errors by hour, weather condition, and season instead of relying only on aggregate RMSE.
5. Before production use, retrain on current data, add lagged demand and event indicators, and validate with rolling-origin backtests.

## Risk boundary

The data cover 2011–2012 and a single system. Residual autocorrelation remains material, heavy-weather estimates are imprecise, and no causal claims are supported. This project is a portfolio demonstration, not a production deployment.


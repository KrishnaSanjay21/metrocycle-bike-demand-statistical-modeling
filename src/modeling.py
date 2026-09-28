from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_squared_log_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.config import (
    BOOTSTRAP_CSV,
    COEFFICIENTS_CSV,
    DIAGNOSTICS_CSV,
    HOLDOUT_FRACTION,
    HYPOTHESES_CSV,
    METRICS_CSV,
    MODEL_BUNDLE,
    PREDICTIONS_CSV,
    RANDOM_SEED,
    ensure_directories,
)
from src.data import read_hourly
from src.features import MODEL_FEATURES, add_model_features, chronological_split

CATEGORICAL_FEATURES = ["hour", "season_code", "month", "weekday", "weather_code"]
CONTINUOUS_FEATURES = [feature for feature in MODEL_FEATURES if feature not in CATEGORICAL_FEATURES]
INFERENCE_FORMULA = (
    "rental_count ~ C(hour) + C(season_code) + C(weather_code) + "
    "year_index + holiday + workingday + temp_c + I(temp_c ** 2) + humidity_pct + "
    "windspeed_scaled + trend_days"
)


@dataclass
class TrainingArtifacts:
    metrics: pd.DataFrame
    predictions: pd.DataFrame
    coefficients: pd.DataFrame
    hypotheses: pd.DataFrame
    diagnostics: pd.DataFrame
    bootstrap: pd.DataFrame


def evaluate_predictions(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    prediction = np.clip(np.asarray(predicted, dtype=float), 0, None)
    truth = np.asarray(actual, dtype=float)
    return {
        "mae": float(mean_absolute_error(truth, prediction)),
        "rmse": float(mean_squared_error(truth, prediction) ** 0.5),
        "rmsle": float(mean_squared_log_error(truth, prediction) ** 0.5),
        "r2": float(r2_score(truth, prediction)),
    }


def _prediction_models() -> tuple[Pipeline, TransformedTargetRegressor, HistGradientBoostingRegressor]:
    transformer = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            (
                "continuous",
                Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler())]),
                CONTINUOUS_FEATURES,
            ),
        ]
    )
    poisson = Pipeline(
        [("features", transformer), ("model", PoissonRegressor(alpha=0.02, max_iter=800))]
    )
    log_linear = TransformedTargetRegressor(
        regressor=Pipeline([("features", transformer), ("model", Ridge(alpha=2.0))]),
        func=np.log1p,
        inverse_func=np.expm1,
    )
    gradient = HistGradientBoostingRegressor(
        learning_rate=0.06,
        max_iter=300,
        max_leaf_nodes=31,
        min_samples_leaf=25,
        l2_regularization=1.0,
        random_state=RANDOM_SEED,
    )
    return poisson, log_linear, gradient


def _baseline_predictions(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    lookup = train.groupby(["hour", "workingday"])["rental_count"].mean()
    overall = float(train["rental_count"].mean())
    return np.array([lookup.get((row.hour, row.workingday), overall) for row in test.itertuples()])


def _coefficient_table(result) -> pd.DataFrame:
    intervals = result.conf_int()
    table = pd.DataFrame(
        {
            "term": result.params.index,
            "coefficient": result.params.values,
            "std_error": result.bse.values,
            "p_value": result.pvalues.values,
            "ci_low": intervals.iloc[:, 0].values,
            "ci_high": intervals.iloc[:, 1].values,
        }
    )
    table["incidence_rate_ratio"] = np.exp(table["coefficient"])
    table["irr_ci_low"] = np.exp(table["ci_low"])
    table["irr_ci_high"] = np.exp(table["ci_high"])
    table["percent_change"] = (table["incidence_rate_ratio"] - 1) * 100
    table["significant_05"] = table["p_value"] < 0.05
    return table


def _wald_test(result, label: str, parameter_names: list[str]) -> dict[str, object]:
    available = [name for name in parameter_names if name in result.params.index]
    if not available:
        return {
            "hypothesis": label,
            "parameters_tested": "",
            "statistic": np.nan,
            "degrees_of_freedom": 0,
            "p_value": np.nan,
            "decision_at_05": "NOT TESTED",
        }
    restriction = ", ".join(f"{name} = 0" for name in available)
    test = result.wald_test(restriction, scalar=True)
    p_value = float(test.pvalue)
    return {
        "hypothesis": label,
        "parameters_tested": " | ".join(available),
        "statistic": float(test.statistic),
        "degrees_of_freedom": len(available),
        "p_value": p_value,
        "decision_at_05": "REJECT H0" if p_value < 0.05 else "FAIL TO REJECT H0",
    }


def _hypothesis_table(result) -> pd.DataFrame:
    hour_terms = [name for name in result.params.index if name.startswith("C(hour)[T.")]
    temp_terms = [name for name in ("temp_c", "I(temp_c ** 2)") if name in result.params.index]
    tests = [
        _wald_test(result, "Rental demand does not vary by hour", hour_terms),
        _wald_test(result, "Temperature has no association with demand", temp_terms),
        _wald_test(result, "Holidays have no association with demand", ["holiday"]),
        _wald_test(result, "Working days have no association with demand", ["workingday"]),
        _wald_test(
            result,
            "Adverse weather has no association with demand",
            ["C(weather_code)[T.3]", "C(weather_code)[T.4]"],
        ),
    ]
    table = pd.DataFrame(tests)
    valid = table["p_value"].notna()
    table.loc[valid, "holm_adjusted_p_value"] = multipletests(
        table.loc[valid, "p_value"].to_numpy(), method="holm"
    )[1]
    table["holm_decision_at_05"] = np.where(
        table["holm_adjusted_p_value"] < 0.05,
        "REJECT H0",
        "FAIL TO REJECT H0",
    )
    return table


def _diagnostic_table(train: pd.DataFrame, poisson_result, nb_result, alpha: float) -> pd.DataFrame:
    pearson_ratio = float(poisson_result.pearson_chi2 / poisson_result.df_resid)
    residuals = np.asarray(nb_result.resid_deviance)
    diagnostics: list[dict[str, object]] = [
        {
            "diagnostic": "Poisson dispersion ratio",
            "value": pearson_ratio,
            "interpretation": "Values materially above 1 indicate overdispersion and support Negative Binomial modeling.",
        },
        {
            "diagnostic": "Estimated NB2 alpha",
            "value": alpha,
            "interpretation": "Positive alpha permits variance to exceed the conditional mean.",
        },
        {
            "diagnostic": "Negative Binomial AIC",
            "value": float(nb_result.aic),
            "interpretation": "Lower values are preferred when comparing models fit to the same data.",
        },
        {
            "diagnostic": "Deviance residual lag-1 autocorrelation",
            "value": float(pd.Series(residuals).autocorr(lag=1)),
            "interpretation": "Material autocorrelation signals remaining temporal structure.",
        },
    ]
    vif_columns = ["temp_c", "humidity_pct", "windspeed_scaled", "trend_days"]
    matrix = train[vif_columns].astype(float)
    matrix = (matrix - matrix.mean()) / matrix.std(ddof=0)
    matrix = sm.add_constant(matrix)
    for index, column in enumerate(matrix.columns):
        if column == "const":
            continue
        diagnostics.append(
            {
                "diagnostic": f"VIF: {column}",
                "value": float(variance_inflation_factor(matrix.values, index)),
                "interpretation": "VIF above 5 deserves review for multicollinearity among modeled continuous predictors.",
            }
        )
    return pd.DataFrame(diagnostics)


def _bootstrap_metrics(predictions: pd.DataFrame, repetitions: int = 500) -> pd.DataFrame:
    rng = np.random.default_rng(RANDOM_SEED)
    rows: list[dict[str, object]] = []
    model_columns = [column for column in predictions if column.startswith("prediction_")]
    n_rows = len(predictions)
    truth = predictions["actual"].to_numpy()
    for column in model_columns:
        values = predictions[column].to_numpy()
        samples = {metric: [] for metric in ("mae", "rmse", "rmsle", "r2")}
        for _ in range(repetitions):
            index = rng.integers(0, n_rows, n_rows)
            result = evaluate_predictions(truth[index], values[index])
            for metric, value in result.items():
                samples[metric].append(value)
        for metric, estimates in samples.items():
            rows.append(
                {
                    "model": column.removeprefix("prediction_").replace("_", " ").title(),
                    "metric": metric,
                    "estimate": evaluate_predictions(truth, values)[metric],
                    "ci_low": float(np.quantile(estimates, 0.025)),
                    "ci_high": float(np.quantile(estimates, 0.975)),
                    "bootstrap_repetitions": repetitions,
                }
            )
    return pd.DataFrame(rows)


def train_models(frame: pd.DataFrame | None = None) -> TrainingArtifacts:
    ensure_directories()
    data = add_model_features(read_hourly() if frame is None else frame)
    train, test = chronological_split(data, HOLDOUT_FRACTION)
    x_train, x_test = train[MODEL_FEATURES], test[MODEL_FEATURES]
    y_train, y_test = train["rental_count"], test["rental_count"]

    poisson_sklearn, log_linear, gradient = _prediction_models()
    poisson_sklearn.fit(x_train, y_train)
    log_linear.fit(x_train, y_train)
    gradient.fit(x_train, y_train)

    statistical_poisson = smf.glm(INFERENCE_FORMULA, data=train, family=sm.families.Poisson()).fit(cov_type="HC1")
    train_mean = np.clip(statistical_poisson.predict(train), 1e-6, None)
    alpha = max(
        float(np.sum((y_train.to_numpy() - train_mean) ** 2 - y_train.to_numpy()) / np.sum(train_mean**2)),
        1e-6,
    )
    statistical_nb = smf.glm(
        INFERENCE_FORMULA,
        data=train,
        family=sm.families.NegativeBinomial(alpha=alpha),
    ).fit(cov_type="HC1")

    predictions = pd.DataFrame(
        {
            "timestamp": test["timestamp"].to_numpy(),
            "actual": y_test.to_numpy(),
            "prediction_baseline": _baseline_predictions(train, test),
            "prediction_log_linear": np.clip(log_linear.predict(x_test), 0, None),
            "prediction_poisson": np.clip(poisson_sklearn.predict(x_test), 0, None),
            "prediction_negative_binomial": np.clip(statistical_nb.predict(test), 0, None),
            "prediction_gradient_boosting": np.clip(gradient.predict(x_test), 0, None),
        }
    )
    model_labels = {
        "prediction_baseline": "Hour/workday baseline",
        "prediction_log_linear": "Log-linear Ridge",
        "prediction_poisson": "Regularized Poisson",
        "prediction_negative_binomial": "Negative Binomial GLM",
        "prediction_gradient_boosting": "Gradient Boosting",
    }
    metric_rows = []
    for column, label in model_labels.items():
        metric_rows.append(
            {
                "model": label,
                **evaluate_predictions(predictions["actual"], predictions[column]),
                "train_rows": len(train),
                "holdout_rows": len(test),
                "train_end": train["timestamp"].max(),
                "holdout_start": test["timestamp"].min(),
                "holdout_end": test["timestamp"].max(),
            }
        )
    metrics = pd.DataFrame(metric_rows).sort_values("rmse").reset_index(drop=True)
    coefficients = _coefficient_table(statistical_nb)
    hypotheses = _hypothesis_table(statistical_nb)
    diagnostics = _diagnostic_table(train, statistical_poisson, statistical_nb, alpha)
    bootstrap = _bootstrap_metrics(predictions)

    metrics.to_csv(METRICS_CSV, index=False)
    predictions.to_csv(PREDICTIONS_CSV, index=False)
    coefficients.to_csv(COEFFICIENTS_CSV, index=False)
    hypotheses.to_csv(HYPOTHESES_CSV, index=False)
    diagnostics.to_csv(DIAGNOSTICS_CSV, index=False)
    bootstrap.to_csv(BOOTSTRAP_CSV, index=False)
    joblib.dump(
        {
            "poisson": poisson_sklearn,
            "log_linear": log_linear,
            "gradient_boosting": gradient,
            "feature_names": MODEL_FEATURES,
            "training_origin": data["timestamp"].min().isoformat(),
            "training_max_trend_days": float(data["trend_days"].max()),
            "holdout_start": test["timestamp"].min().isoformat(),
        },
        MODEL_BUNDLE,
    )
    return TrainingArtifacts(metrics, predictions, coefficients, hypotheses, diagnostics, bootstrap)


if __name__ == "__main__":
    train_models()

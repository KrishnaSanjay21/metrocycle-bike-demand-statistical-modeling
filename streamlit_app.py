from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.bootstrap import ensure_project_ready
from src.config import (
    BOOTSTRAP_CSV,
    COEFFICIENTS_CSV,
    DATASET_DOI,
    DIAGNOSTICS_CSV,
    HYPOTHESES_CSV,
    METRICS_CSV,
    MODEL_BUNDLE,
    PREDICTIONS_CSV,
    UCI_DATASET_PAGE,
)
from src.data import read_daily_summary, read_hourly, read_quality_results
from src.features import MODEL_FEATURES

st.set_page_config(page_title="MetroCycle Statistical Modeling", page_icon="🚲", layout="wide")

NAVY = "#132238"
BLUE = "#246BFD"
TEAL = "#1F9D8A"
ORANGE = "#F39C4A"
RED = "#D9544D"
LIGHT = "#F4F7FB"

st.markdown(
    f"""
    <style>
      .stApp {{ background: {LIGHT}; color: {NAVY}; }}
      [data-testid="stAppViewContainer"] h1,
      [data-testid="stAppViewContainer"] h2,
      [data-testid="stAppViewContainer"] h3,
      [data-testid="stAppViewContainer"] p,
      [data-testid="stAppViewContainer"] label {{ color: {NAVY} !important; }}
      [data-testid="stMetric"] {{
        background: white; border: 1px solid #DCE5EF; border-radius: 14px;
        padding: 16px; box-shadow: 0 3px 10px rgba(19,34,56,.05);
      }}
      [data-testid="stMetricLabel"] p {{ color: #52677D !important; }}
      [data-testid="stMetricValue"], [data-testid="stMetricValue"] div {{
        color: {NAVY} !important; font-size: 1.65rem !important;
      }}
      .method-note {{ background: white; border-left: 4px solid {BLUE}; padding: 13px 16px;
        border-radius: 8px; color: #334A61; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def show_chart(fig: go.Figure, height: int | None = None) -> None:
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(color=NAVY),
        title_font=dict(color=NAVY),
        margin=dict(l=10, r=10, t=55, b=10),
    )
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, width="stretch", theme=None)


@st.cache_resource(show_spinner=False)
def prepare_project() -> None:
    ensure_project_ready()


@st.cache_data(show_spinner=False)
def load_data():
    return {
        "hourly": read_hourly(),
        "daily": read_daily_summary(),
        "quality": read_quality_results(),
        "metrics": pd.read_csv(METRICS_CSV),
        "predictions": pd.read_csv(PREDICTIONS_CSV, parse_dates=["timestamp"]),
        "coefficients": pd.read_csv(COEFFICIENTS_CSV),
        "hypotheses": pd.read_csv(HYPOTHESES_CSV),
        "diagnostics": pd.read_csv(DIAGNOSTICS_CSV),
        "bootstrap": pd.read_csv(BOOTSTRAP_CSV),
    }


@st.cache_resource(show_spinner=False)
def load_models():
    return joblib.load(MODEL_BUNDLE)


try:
    with st.spinner("Preparing the public dataset and statistical models on first launch…"):
        prepare_project()
except Exception as exc:
    st.error("MetroCycle could not prepare its analytical artifacts.")
    st.caption(f"{type(exc).__name__}: {exc}")
    st.stop()

data = load_data()
hourly = data["hourly"]

page = st.sidebar.radio(
    "View",
    ["Executive Overview", "Statistical Inference", "Model Diagnostics", "Scenario Explorer", "Data Quality"],
)
st.sidebar.caption("Published UCI Bike Sharing data · Capital Bikeshare · 2011–2012")
st.sidebar.markdown(f"[Dataset source]({UCI_DATASET_PAGE})")

if page == "Executive Overview":
    st.title("MetroCycle")
    st.caption("Bike-demand statistical modeling and operational forecasting")
    st.markdown(
        '<div class="method-note">Count models estimate associations between hourly demand, weather, and calendar conditions. The chronological holdout preserves time order and avoids random-split leakage.</div>',
        unsafe_allow_html=True,
    )
    peak = hourly.groupby("hour")["rental_count"].mean().idxmax()
    cols = st.columns(5)
    cols[0].metric("Hourly observations", f"{len(hourly):,}")
    cols[1].metric("Total rentals", f"{hourly['rental_count'].sum():,.0f}")
    cols[2].metric("Average per hour", f"{hourly['rental_count'].mean():,.1f}")
    cols[3].metric("Peak average hour", f"{int(peak):02d}:00")
    cols[4].metric("Best holdout model", data["metrics"].iloc[0]["model"])

    left, right = st.columns([1.35, 1])
    with left:
        daily = data["daily"]
        fig = px.line(
            daily,
            x="service_date",
            y="total_rentals",
            color_discrete_sequence=[BLUE],
            title="Daily rental demand",
            labels={"service_date": "Date", "total_rentals": "Rentals"},
        )
        fig.update_yaxes(title="Rentals")
        show_chart(fig, 420)
    with right:
        profile = hourly.groupby(["hour", "workingday"], as_index=False)["rental_count"].mean()
        profile["Day type"] = profile["workingday"].map({1: "Working day", 0: "Weekend / holiday"})
        fig = px.line(
            profile,
            x="hour",
            y="rental_count",
            color="Day type",
            markers=True,
            color_discrete_sequence=[BLUE, ORANGE],
            title="Average hourly demand profile",
            labels={"rental_count": "Average rentals", "hour": "Hour"},
        )
        show_chart(fig, 420)

    weather = hourly.groupby("weather", as_index=False).agg(
        average_rentals=("rental_count", "mean"), observations=("rental_count", "size")
    )
    fig = px.bar(
        weather.sort_values("average_rentals"),
        x="average_rentals",
        y="weather",
        orientation="h",
        color="average_rentals",
        color_continuous_scale=[[0, "#C9D8F5"], [1, BLUE]],
        title="Observed average demand by weather condition",
        labels={"average_rentals": "Average hourly rentals", "weather": "Weather"},
    )
    show_chart(fig, 360)

elif page == "Statistical Inference":
    st.title("Statistical Inference")
    st.caption("Negative Binomial GLM with heteroskedasticity-robust confidence intervals")
    st.markdown(
        '<div class="method-note">Incidence-rate ratios (IRRs) describe conditional associations, not causal effects. An IRR of 1.20 corresponds to approximately 20% higher expected demand, holding modeled covariates constant.</div>',
        unsafe_allow_html=True,
    )

    coefficients = data["coefficients"].copy()
    focus = coefficients[
        coefficients["term"].str.contains("weather_code|season_code|holiday|workingday|temp_c|humidity_pct|windspeed", regex=True)
    ].copy()
    focus = focus.replace([np.inf, -np.inf], np.nan).dropna(subset=["incidence_rate_ratio", "irr_ci_low", "irr_ci_high"])
    focus["display_term"] = (
        focus["term"]
        .str.replace("C(weather_code)", "Weather", regex=False)
        .str.replace("C(season_code)", "Season", regex=False)
        .str.replace("[T.", " = ", regex=False)
        .str.replace("]", "", regex=False)
        .str.replace("humidity_pct", "Humidity (1 percentage point)", regex=False)
        .str.replace("windspeed_scaled", "Wind speed (1 scaled unit)", regex=False)
        .str.replace("workingday", "Working day", regex=False)
        .str.replace("holiday", "Holiday", regex=False)
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=focus["incidence_rate_ratio"],
            y=focus["display_term"],
            mode="markers",
            marker=dict(color=np.where(focus["significant_05"], BLUE, "#9BAABA"), size=9),
            error_x=dict(
                type="data",
                symmetric=False,
                array=focus["irr_ci_high"] - focus["incidence_rate_ratio"],
                arrayminus=focus["incidence_rate_ratio"] - focus["irr_ci_low"],
            ),
            hovertemplate="%{y}<br>IRR=%{x:.3f}<extra></extra>",
        )
    )
    fig.add_vline(x=1, line_dash="dash", line_color=RED)
    fig.update_xaxes(title="Incidence-rate ratio (95% CI)")
    fig.update_yaxes(title="")
    fig.update_layout(title="Selected adjusted associations")
    show_chart(fig, max(460, len(focus) * 30))

    st.subheader("Pre-specified hypothesis tests")
    hypotheses = data["hypotheses"].copy()
    hypotheses["p_value"] = hypotheses["p_value"].map(lambda value: f"{value:.4g}" if pd.notna(value) else "—")
    hypotheses["holm_adjusted_p_value"] = hypotheses["holm_adjusted_p_value"].map(
        lambda value: f"{value:.4g}" if pd.notna(value) else "—"
    )
    st.dataframe(
        hypotheses[
            ["hypothesis", "statistic", "degrees_of_freedom", "p_value", "holm_adjusted_p_value", "holm_decision_at_05"]
        ],
        width="stretch",
        hide_index=True,
    )

    st.subheader("Coefficient detail")
    st.dataframe(
        coefficients[["term", "coefficient", "std_error", "p_value", "incidence_rate_ratio", "irr_ci_low", "irr_ci_high"]],
        width="stretch",
        hide_index=True,
        column_config={
            "coefficient": st.column_config.NumberColumn(format="%.4f"),
            "std_error": st.column_config.NumberColumn(format="%.4f"),
            "p_value": st.column_config.NumberColumn(format="%.4g"),
            "incidence_rate_ratio": st.column_config.NumberColumn(format="%.3f"),
            "irr_ci_low": st.column_config.NumberColumn(format="%.3f"),
            "irr_ci_high": st.column_config.NumberColumn(format="%.3f"),
        },
    )

elif page == "Model Diagnostics":
    st.title("Model Diagnostics")
    st.caption("Chronological holdout performance, uncertainty, and specification checks")
    metrics = data["metrics"]
    best = metrics.iloc[0]
    dispersion = data["diagnostics"].loc[
        data["diagnostics"]["diagnostic"] == "Poisson dispersion ratio", "value"
    ].iloc[0]
    cols = st.columns(4)
    cols[0].metric("Best model", best["model"])
    cols[1].metric("Holdout RMSE", f"{best['rmse']:.1f}")
    cols[2].metric("Holdout MAE", f"{best['mae']:.1f}")
    cols[3].metric("Poisson dispersion", f"{dispersion:.1f}×")

    left, right = st.columns(2)
    with left:
        melted = metrics.melt(id_vars="model", value_vars=["mae", "rmse"], var_name="metric", value_name="value")
        fig = px.bar(
            melted,
            x="model",
            y="value",
            color="metric",
            barmode="group",
            color_discrete_map={"mae": TEAL, "rmse": BLUE},
            title="Chronological holdout error",
            labels={"value": "Error (rentals)", "model": "Model"},
        )
        fig.update_xaxes(tickangle=-20)
        show_chart(fig, 430)
    with right:
        boot = data["bootstrap"]
        rmse = boot[boot["metric"] == "rmse"].copy()
        fig = go.Figure(
            go.Scatter(
                x=rmse["estimate"],
                y=rmse["model"],
                mode="markers",
                marker=dict(color=BLUE, size=9),
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=rmse["ci_high"] - rmse["estimate"],
                    arrayminus=rmse["estimate"] - rmse["ci_low"],
                ),
            )
        )
        fig.update_layout(title="Bootstrap 95% intervals for holdout RMSE")
        fig.update_xaxes(title="RMSE")
        fig.update_yaxes(title="")
        show_chart(fig, 430)

    predictions = data["predictions"].copy()
    recent = predictions.tail(24 * 14)
    fig = px.line(
        recent,
        x="timestamp",
        y=["actual", "prediction_negative_binomial", "prediction_gradient_boosting"],
        color_discrete_sequence=[NAVY, ORANGE, BLUE],
        title="Last 14 holdout days: actual versus predicted demand",
        labels={"value": "Hourly rentals", "variable": "Series"},
    )
    show_chart(fig, 420)

    st.subheader("Specification diagnostics")
    st.dataframe(data["diagnostics"], width="stretch", hide_index=True)

elif page == "Scenario Explorer":
    st.title("Scenario Explorer")
    st.caption("Compare model predictions for a user-defined operating scenario")
    st.warning("Scenario estimates are predictive associations, not causal forecasts or policy effects.")
    c1, c2, c3, c4 = st.columns(4)
    hour = c1.slider("Hour", 0, 23, 8)
    season_code = c2.selectbox("Season", [1, 2, 3, 4], format_func=lambda value: {1: "Winter", 2: "Spring", 3: "Summer", 4: "Fall"}[value])
    weather_code = c3.selectbox(
        "Weather",
        [1, 2, 3, 4],
        format_func=lambda value: {1: "Clear", 2: "Mist / cloudy", 3: "Light rain or snow", 4: "Heavy weather"}[value],
    )
    workingday = c4.toggle("Working day", value=True)
    c5, c6, c7 = st.columns(3)
    temp_c = c5.slider("Temperature (°C)", -8.0, 39.0, 20.0, 0.5)
    humidity_pct = c6.slider("Humidity (%)", 0, 100, 60)
    windspeed_scaled = c7.slider("Wind-speed index", 0.0, 67.0, 12.0, 0.5)

    bundle = load_models()
    month = {1: 1, 2: 4, 3: 7, 4: 10}[season_code]
    scenario = pd.DataFrame(
        [
            {
                "hour": hour,
                "season_code": season_code,
                "year_index": 1,
                "month": month,
                "holiday": 0,
                "weekday": 1,
                "workingday": int(workingday),
                "weather_code": weather_code,
                "temp_c": temp_c,
                "feels_like_c": temp_c,
                "humidity_pct": humidity_pct,
                "windspeed_scaled": windspeed_scaled,
                "hour_sin": np.sin(2 * np.pi * hour / 24),
                "hour_cos": np.cos(2 * np.pi * hour / 24),
                "month_sin": np.sin(2 * np.pi * month / 12),
                "month_cos": np.cos(2 * np.pi * month / 12),
                "trend_days": bundle["training_max_trend_days"],
            }
        ],
        columns=MODEL_FEATURES,
    )
    scenario_predictions = pd.DataFrame(
        {
            "Model": ["Log-linear Ridge", "Regularized Poisson", "Gradient Boosting"],
            "Predicted rentals": [
                max(0.0, float(bundle["log_linear"].predict(scenario)[0])),
                max(0.0, float(bundle["poisson"].predict(scenario)[0])),
                max(0.0, float(bundle["gradient_boosting"].predict(scenario)[0])),
            ],
        }
    )
    fig = px.bar(
        scenario_predictions,
        x="Model",
        y="Predicted rentals",
        color="Model",
        color_discrete_sequence=[TEAL, ORANGE, BLUE],
        text_auto=".0f",
        title="Predicted hourly demand under the selected scenario",
    )
    show_chart(fig, 430)
    st.dataframe(scenario_predictions, width="stretch", hide_index=True)

else:
    st.title("Data Quality & Methodology")
    quality = data["quality"]
    passed = int((quality["status"] == "PASS").sum())
    cols = st.columns(3)
    cols[0].metric("Checks passed", f"{passed} of {len(quality)}")
    cols[1].metric("Critical failures", int(((quality["severity"] == "Critical") & (quality["status"] != "PASS")).sum()))
    cols[2].metric("Source rows", f"{len(hourly):,}")
    st.dataframe(quality, width="stretch", hide_index=True)

    st.subheader("Published source")
    st.markdown(f"[UCI Bike Sharing dataset]({UCI_DATASET_PAGE}) · [DOI]({DATASET_DOI})")
    st.write(
        "The file contains hourly Capital Bikeshare rental counts for 2011–2012 with calendar and weather variables. "
        "Casual and registered counts are retained for reconciliation but excluded from predictors because they sum to the target."
    )
    st.subheader("Validation design")
    metrics = data["metrics"]
    st.write(
        f"Models train through {pd.to_datetime(metrics.iloc[0]['train_end']).date()} and are evaluated from "
        f"{pd.to_datetime(metrics.iloc[0]['holdout_start']).date()} through {pd.to_datetime(metrics.iloc[0]['holdout_end']).date()}. "
        "Bootstrap confidence intervals resample holdout rows and therefore quantify metric uncertainty for this holdout period."
    )
    st.subheader("Limitations")
    st.write(
        "The data cover one system and an older historical period. Weather and calendar coefficients are associational; omitted variables, "
        "system expansion, and temporal dependence limit causal interpretation and future generalization."
    )

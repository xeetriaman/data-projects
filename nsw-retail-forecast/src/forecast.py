"""Forecast NSW retail turnover a year ahead and compare with a simple baseline.

Usage:
    python src/forecast.py

Backtest: for each of the last three financial years, every industry series is trained only on
months before that year and forecast 12 months ahead with Holt-Winters exponential smoothing.
The baseline repeats the same month one year earlier (seasonal naive). Writes
outputs/forecasts.csv (the latest year, for charts) and outputs/metrics.json.
"""

import json
import os

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = os.path.join(os.path.dirname(__file__), "..")
HORIZON = 12
TEST_YEARS = 3  # rolling origins: FY2023, FY2024, FY2025
TRAIN_FROM = "2010-01-01"  # recent enough to reflect today's shopping, long enough for 14 full seasons


def split(series: pd.Series, years_back: int = 0, horizon: int = HORIZON) -> tuple[pd.Series, pd.Series]:
    """Test on the 12 months ending `years_back` years before the series ends; train on everything earlier."""
    end = len(series) - years_back * 12
    return series.iloc[: end - horizon], series.iloc[end - horizon : end]


def seasonal_naive(train: pd.Series, horizon: int = HORIZON) -> np.ndarray:
    """Forecast each month as the same month one year earlier."""
    return train.iloc[-12:].to_numpy()[:horizon]


def holt_winters(train: pd.Series, horizon: int = HORIZON) -> np.ndarray:
    """Damped additive trend with multiplicative yearly seasonality."""
    model = ExponentialSmoothing(train, trend="add", damped_trend=True, seasonal="mul", seasonal_periods=12)
    return model.fit(optimized=True).forecast(horizon).to_numpy()


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean absolute percentage error, in percent."""
    actual, predicted = np.asarray(actual, float), np.asarray(predicted, float)
    return float(np.mean(np.abs(predicted - actual) / actual) * 100)


def main() -> None:
    data = pd.read_csv(os.path.join(ROOT, "data", "retail.csv"), parse_dates=["month"])
    data = data[data["month"] >= TRAIN_FROM]

    rows, errors = [], []
    for industry, group in data.groupby("industry"):
        series = group.set_index("month")["turnover_m"].asfreq("MS")
        for years_back in range(TEST_YEARS):
            train, test = split(series, years_back)
            forecasts = {"holt_winters": holt_winters(train), "seasonal_naive": seasonal_naive(train)}
            test_year = f"FY{test.index[-1].year}"
            errors += [{"industry": industry, "test_year": test_year, "model": name, "mape": mape(test, f)} for name, f in forecasts.items()]
            if years_back == 0:
                rows.append(pd.DataFrame({"month": test.index, "industry": industry, "actual": test.to_numpy(), **forecasts}))
    errors = pd.DataFrame(errors)
    out = os.path.join(ROOT, "outputs")
    os.makedirs(out, exist_ok=True)
    forecasts = pd.concat(rows).round({"actual": 1, "holt_winters": 1, "seasonal_naive": 1})
    forecasts.to_csv(os.path.join(out, "forecasts.csv"), index=False, date_format="%Y-%m")

    by_industry = errors.pivot_table(index="industry", columns="model", values="mape").round(2)
    by_year = errors[errors["industry"] != "Total retail"].pivot_table(index="test_year", columns="model", values="mape").round(2)
    groups = by_industry.drop(index="Total retail")
    summary = {
        "train_from": TRAIN_FROM[:7],
        "test_years": list(by_year.index),
        "average_over_groups": groups.mean().round(2).to_dict(),
        "groups_where_holt_winters_wins": int((groups["holt_winters"] < groups["seasonal_naive"]).sum()),
        "by_industry": by_industry.to_dict(orient="index"),
        "by_test_year": by_year.to_dict(orient="index"),
    }
    with open(os.path.join(out, "metrics.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

"""Predict Sydney house sale prices and test the models on later sales they never saw.

Usage:
    python src/model.py

Trains on contracts up to 30 June 2018 and tests on July-December 2018.
Writes outputs/metrics.json and outputs/test_predictions.csv.
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

ROOT = os.path.join(os.path.dirname(__file__), "..")
SPLIT_DATE = "2018-07-01"
MIN_SUBURB_SALES = 5  # suburbs with fewer training sales fall back to their postcode


def load() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(ROOT, "data", "sales.csv"), parse_dates=["contract_date"])
    df["log_price"] = np.log(df["price"])
    df["log_area"] = np.log(df["area_sqm"])
    df["month_index"] = (df["contract_date"].dt.year - 2017) * 12 + df["contract_date"].dt.month
    return df


def split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_train = df["contract_date"] < SPLIT_DATE
    return df[is_train].copy(), df[~is_train].copy()


def location_level(train: pd.DataFrame, rows: pd.DataFrame) -> pd.Series:
    """Median log price of the suburb in the training data, falling back to postcode, then Sydney overall.

    Learned from training sales only, so no test prices leak into the feature.
    """
    by_suburb = train.groupby("suburb")["log_price"].agg(["median", "size"])
    by_suburb = by_suburb.loc[by_suburb["size"] >= MIN_SUBURB_SALES, "median"]
    by_postcode = train.groupby("postcode")["log_price"].median()
    level = rows["suburb"].map(by_suburb)
    level = level.fillna(rows["postcode"].map(by_postcode))
    return level.fillna(train["log_price"].median())


def features(train: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    zones = pd.get_dummies(rows["zoning"], prefix="zone").reindex(
        columns=[f"zone_{z}" for z in sorted(train["zoning"].unique())], fill_value=0
    )
    return pd.concat(
        [pd.DataFrame({"location": location_level(train, rows),
                       "log_area": rows["log_area"],
                       "month_index": rows["month_index"]}, index=rows.index),
         zones.astype(float)],
        axis=1,
    )


def scores(actual: pd.Series, predicted: np.ndarray) -> dict:
    error = np.abs(predicted - actual) / actual
    return {
        "median_abs_pct_error": round(float(np.median(error)) * 100, 1),
        "within_10_pct": round(float((error <= 0.10).mean()) * 100, 1),
        "mae_dollars": int(np.mean(np.abs(predicted - actual))),
        "median_predicted_to_actual": round(float(np.median(predicted / actual)), 3),
    }


def main() -> None:
    train, test = split(load())
    x_train, x_test = features(train, train), features(train, test)

    predictions = {
        "Baseline: suburb median": np.exp(location_level(train, test)).to_numpy(),
        "Linear regression": np.exp(
            LinearRegression().fit(x_train, train["log_price"]).predict(x_test)),
        "Gradient boosting": np.exp(
            HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, random_state=0)
            .fit(x_train, train["log_price"]).predict(x_test)),
    }

    metrics = {
        "train_sales": len(train),
        "test_sales": len(test),
        "split_date": SPLIT_DATE,
        "models": {name: scores(test["price"], p) for name, p in predictions.items()},
    }
    out = os.path.join(ROOT, "outputs")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    test.assign(predicted=predictions["Gradient boosting"].round(-3).astype(int))[
        ["contract_date", "suburb", "area_sqm", "price", "predicted"]
    ].to_csv(os.path.join(out, "test_predictions.csv"), index=False)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()

"""Download NSW monthly retail turnover by industry from the ABS Data API.

Usage:
    python src/fetch_data.py

Writes data/retail.csv with one row per month and industry group:
month (YYYY-MM-01), industry, turnover_m (current prices, $ million, original series).
"""

import io
import os
import urllib.request

import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")

# Retail Trade, Australia (ABS dataflow RT): current prices, original series, New South Wales, monthly.
INDUSTRIES = {
    "20": "Total retail",
    "41": "Food retailing",
    "42": "Household goods",
    "43": "Clothing, footwear and accessories",
    "44": "Department stores",
    "45": "Other retailing",
    "46": "Cafes, restaurants and takeaway",
}
URL = "https://data.api.abs.gov.au/rest/data/ABS,RT,1.0.0/M1.{codes}.10.1.M?format=csv"


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep month, industry name and turnover, sorted by industry then month."""
    out = pd.DataFrame(
        {
            "month": pd.to_datetime(raw["TIME_PERIOD"], format="%Y-%m"),
            "industry": raw["INDUSTRY"].astype(str).str.zfill(2).map(INDUSTRIES),
            "turnover_m": raw["OBS_VALUE"].astype(float),
        }
    )
    return out.dropna().sort_values(["industry", "month"]).reset_index(drop=True)


def main() -> None:
    with urllib.request.urlopen(URL.format(codes="+".join(INDUSTRIES))) as response:
        raw = pd.read_csv(io.StringIO(response.read().decode("utf-8")), dtype={"INDUSTRY": str})
    data = tidy(raw)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    data.to_csv(os.path.join(ROOT, "data", "retail.csv"), index=False, date_format="%Y-%m-%d")
    print(f"{len(data):,} rows, {data['month'].min():%b %Y} to {data['month'].max():%b %Y}")


if __name__ == "__main__":
    main()

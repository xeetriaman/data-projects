"""Turn the NSW Valuer General bulk sales file into a clean table of Sydney house sales.

Usage:
    python src/build_dataset.py path/to/PropertySales2018.tsv

Writes data/sales.csv with one row per arm's-length house sale.
"""

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")

# Greater Sydney postcode ranges (Australia Post).
SYDNEY_POSTCODES = [(2000, 2249), (2555, 2574), (2740, 2786)]
MIN_PRICE, MAX_PRICE = 150_000, 20_000_000
MIN_AREA, MAX_AREA = 100, 5_000


def is_sydney(postcode: pd.Series) -> pd.Series:
    return np.logical_or.reduce([postcode.between(lo, hi) for lo, hi in SYDNEY_POSTCODES])


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep whole-property, arm's-length sales of houses in Greater Sydney with plausible values."""
    df = raw.assign(
        contract_date=pd.to_datetime(raw["Contract_date"], errors="coerce"),
        postcode=pd.to_numeric(raw["Postcode"], errors="coerce"),
    )
    keep = (
        (df["Nature_of_property"] == "Residence")
        & df["Unit_no"].isna()                       # units have a unit number
        & df["Strata_lot_no"].isna()                 # and a strata lot
        & df["Sale_code"].isna()                     # coded sales are not arm's length
        & (df["Percent_interest_of_sale"].fillna(0) == 0)  # 0 means the whole property
        & df["Purchase_price"].between(MIN_PRICE, MAX_PRICE)
        & df["Area_sqm"].between(MIN_AREA, MAX_AREA)
        & df["contract_date"].dt.year.between(2017, 2018)
        & is_sydney(df["postcode"])
    )
    out = df.loc[keep].drop_duplicates(subset=["Property_id", "contract_date", "Purchase_price"])
    return pd.DataFrame({
        "contract_date": out["contract_date"].dt.date,
        "suburb": out["Locality"].str.title(),
        "postcode": out["postcode"].astype(int),
        "zoning": out["Zoning"].fillna("Unknown"),
        "area_sqm": out["Area_sqm"].round(1),
        "price": out["Purchase_price"].astype(int),
    }).sort_values("contract_date").reset_index(drop=True)


def main(path: str) -> None:
    raw = pd.read_csv(path, sep="\t", low_memory=False)
    sales = clean(raw)
    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    sales.to_csv(os.path.join(ROOT, "data", "sales.csv"), index=False)
    print(f"{len(raw):,} raw records -> {len(sales):,} Sydney house sales")


if __name__ == "__main__":
    main(sys.argv[1])

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from build_dataset import clean  # noqa: E402
from model import location_level, split  # noqa: E402


def raw_row(**overrides):
    row = {
        "Contract_date": "2018-03-01", "Postcode": 2000, "Nature_of_property": "Residence",
        "Unit_no": np.nan, "Strata_lot_no": np.nan, "Sale_code": np.nan,
        "Percent_interest_of_sale": 0, "Purchase_price": 1_000_000, "Area_sqm": 500,
        "Property_id": 1, "Locality": "SYDNEY", "Zoning": "General Residential",
    }
    row.update(overrides)
    return row


def test_clean_keeps_only_arms_length_sydney_houses():
    raw = pd.DataFrame([
        raw_row(),
        raw_row(Property_id=2, Unit_no="5"),          # a unit
        raw_row(Property_id=3, Sale_code="XA"),       # not arm's length
        raw_row(Property_id=4, Postcode=2795),        # Bathurst, outside Sydney
        raw_row(Property_id=5, Purchase_price=1000),  # implausible price
        raw_row(Property_id=6, Percent_interest_of_sale=50),  # part share
        raw_row(),                                    # exact duplicate
    ])
    out = clean(raw)
    assert len(out) == 1
    assert out.loc[0, "suburb"] == "Sydney"


def sales(rows):
    df = pd.DataFrame(rows, columns=["suburb", "postcode", "price"])
    df["log_price"] = np.log(df["price"])
    return df


def test_location_level_falls_back_from_suburb_to_postcode_to_overall():
    train = sales([("A", 2000, 1e6)] * 5 + [("B", 2001, 4e5)] * 2)
    rows = sales([("A", 2000, 1), ("B", 2001, 1), ("C", 2002, 1)])
    level = np.exp(location_level(train, rows))
    assert round(level[0]) == 1e6          # suburb A has 5 sales: suburb median
    assert round(level[1]) == 4e5          # suburb B has 2 sales: postcode median
    assert round(level[2]) == 1e6          # unseen postcode: Sydney-wide median


def test_location_level_ignores_test_prices():
    train = sales([("A", 2000, 1e6)] * 5)
    a = location_level(train, sales([("A", 2000, 1)]))
    b = location_level(train, sales([("A", 2000, 9e9)]))
    assert a.equals(b)


def test_split_is_by_date():
    df = pd.DataFrame({"contract_date": pd.to_datetime(["2018-06-30", "2018-07-01"])})
    train, test = split(df)
    assert len(train) == 1 and len(test) == 1
    assert train["contract_date"].max() < test["contract_date"].min()
